"""Extract Pokédex entries and machine labels from the release engine snapshot."""

import argparse
import json
import re
import shutil
import struct
from pathlib import Path


ENGINE = Path(__file__).resolve().parents[2] / "HG-Engine"
STAT_FIELDS = ("hp", "attack", "defense", "spAttack", "spDefense", "speed")
MACHINE_CODE = r"(?:TM|HM|TR)\d{2,3}(?:_[A-Z]+)?"


def source(path):
    return (ENGINE / path).read_text(encoding="utf-8")


def entries(text, prefix):
    parts = re.split(r"(?m)^\s*\[(" + prefix + r"\w+)\]\s*=\s*\{", text)
    return dict(zip(parts[1::2], parts[2::2]))


def field(block, name, pattern):
    return re.search(r"\." + name + r"\s*=\s*(" + pattern + r")", block).group(1)


def c_string(block, name):
    value = json.loads(field(block, name, r'"(?:\\.|[^"\\])*"'))
    return " ".join(value.replace(r"\n", " ").split())


def display(token, prefix):
    return token.removeprefix(prefix).replace("_", " ").title()


def species_name(token, block, base, blocks):
    name = c_string(block, "name")
    if token == base:
        return name if name != "-----" else display(token, "SPECIES_")
    base_name = c_string(blocks[base], "name")
    for region in ("ALOLAN", "GALARIAN", "HISUIAN", "PALDEAN"):
        if token == f"{base}_{region}":
            return f"{region.title()} {base_name}"
    if token.startswith("SPECIES_MEGA_"):
        variant = token[len("SPECIES_MEGA_"):].removeprefix(base.removeprefix("SPECIES_")).strip("_")
        suffix = f" {variant.replace('_', ' ').title()}" if variant else ""
        return f"Mega {base_name}{suffix}"
    if token.startswith(base + "_"):
        return f"{base_name} ({display(token, base + '_')})"
    return name if name != "-----" and name != base_name else display(token, "SPECIES_")


def move_tables():
    names = {token: c_string(block, "fullName")
             for token, block in entries(source("data/Moves.c"), "MOVE_").items()}
    table = source("data/MachineMoves.c").split("sMachineMoves[] = {", 1)[1].split("};", 1)[0]
    machines = [(code, move) for move, code in re.findall(
        rf"(?m)^\s*(MOVE_\w+),\s*//\s*({MACHINE_CODE})\b", table)]
    # The offsets follow ItemToMachineMoveIndex in src/item.c.
    expected = ([f"TM{i:03}" for i in range(1, 93)] + [f"HM{i:02}" for i in range(1, 9)]
                + ["HM07_ORAS", "TM00"] + [f"TM{i:03}" for i in range(93, 101)]
                + ["TM100_SV"] + [f"TM{i:03}" for i in range(101, 230)]
                + [f"TR{i:02}" for i in range(100)])
    if [code for code, _ in machines] != expected:
        raise ValueError("Machine move order changed; review the engine's item to machine mapping")
    table = source("src/field/move_tutor.c").split("sTutorMoves[] = {", 1)[1].split("};", 1)[0]
    tutors = list(dict.fromkeys(re.findall(r"\{\s*(MOVE_\w+),", table)))
    return names, machines, tutors


def stats(block, name):
    values = field(block, name, r"\{[^}]+\}")
    return [int(field(values, stat, r"\d+")) for stat in STAT_FIELDS]


def labels(block, name, prefix):
    values = field(block, name, r"\{[^}]+\}")
    return [display(token, prefix) for token in dict.fromkeys(re.findall(prefix + r"\w+", values))
            if token != prefix + "NONE"]


def sprite_for(export, token):
    stem = token.removeprefix("SPECIES_").lower()
    for folder in ("ColorIcons", "TrainerMegaIcons", "Pokemon"):
        path = f"Sprites/{folder}/{stem}.png"
        if (export / path).is_file():
            return path
    return ""


def is_battle_sheet(path):
    try:
        with path.open("rb") as stream:
            header = stream.read(24)
    except FileNotFoundError:
        return False
    return (len(header) == 24 and header.startswith(b"\x89PNG\r\n\x1a\n")
            and header[12:16] == b"IHDR" and struct.unpack(">II", header[16:24]) == (160, 80))


def front_sprite_for(export, token):
    stem = token.removeprefix("SPECIES_").lower()
    for folder in ("Front", "TrainerMegaFront", "PokedexFront"):
        path = f"Sprites/{folder}/{stem}.png"
        if is_battle_sheet(export / path):
            return path
    return ""


def read_pokedex(export=None):
    names, machines, tutors = move_tables()
    blocks = entries(source("data/Species.c"), "SPECIES_")
    forms = dict(re.findall(r"\[(SPECIES_\w+)\s*-\s*SPECIES_MEGA_START\]\s*=\s*(SPECIES_\w+)",
                            source("data/FormToSpeciesMapping.c")))
    hidden = dict(re.findall(r"\[(SPECIES_\w+)\s*\]\s*=\s*(ABILITY_\w+)",
                             source("data/HiddenAbilityTable.c")))
    learnsets = json.loads(source("data/learnsets/learnsets.json"))
    pokemon = []
    for token, block in blocks.items():
        base_stats = stats(block, "baseStats")
        if (not sum(base_stats) or token in {"SPECIES_EGG", "SPECIES_BAD_EGG"}
                or "_FILLER_" in token):
            continue  # The engine reserves these entries for internal use.
        base = forms.get(token, token)
        base_set = learnsets.get(base, {})
        own_set = learnsets.get(token, {})
        # The engine falls back per category, then enables any machine whose move is also learned by level.
        level = own_set.get("LevelMoves") or base_set.get("LevelMoves", [])
        machine_moves = set(own_set.get("MachineMoves") or base_set.get("MachineMoves", []))
        machine_moves.update(row["Move"] for row in level)
        egg = own_set.get("EggMoves") or base_set.get("EggMoves", [])
        tutor = set(own_set.get("TutorMoves") or base_set.get("TutorMoves", []))
        hidden_ability = hidden.get(token, "ABILITY_NONE")
        mon = {
            "token": token, "name": species_name(token, block, base, blocks), "form": token != base,
            "types": labels(block, "types", "TYPE_"), "stats": base_stats,
            "abilities": labels(block, "abilities", "ABILITY_"),
            "hidden": display(hidden_ability, "ABILITY_") if hidden_ability != "ABILITY_NONE" else "",
            "category": c_string(block, "classification"), "description": c_string(block, "pokedexEntry"),
            "height": c_string(block, "height"), "weight": c_string(block, "weight"),
            "catchRate": int(field(block, "catchRate", r"\d+")),
            "friendship": int(field(block, "baseFriendship", r"\d+")),
            "growth": display(field(block, "expRate", r"GROWTH_\w+"), "GROWTH_"),
            "eggGroups": labels(block, "eggGroups", "EGG_GROUP_"), "evs": stats(block, "evYields"),
            "level": [[row["Level"], names[row["Move"]]] for row in level],
            "machines": [code for code, move in machines if move in machine_moves],
            "egg": [names[move] for move in egg],
            "tutor": [names[move] for move in tutors if move in tutor],
        }
        for key in ("category", "description", "height", "weight"):
            if "?" in mon[key][:3] or mon[key] == "-----":
                mon[key] = ""
        if export is not None:
            mon["icon"] = sprite_for(export, token)
            mon["front"] = front_sprite_for(export, token)
        pokemon.append(mon)
    return {"pokemon": pokemon, "machineMoves": {code: names[move] for code, move in machines}}


def copy_missing_battle_sprites(export, engine_sprites):
    folder = export / "Sprites" / "PokedexFront"
    folder.mkdir(parents=True, exist_ok=True)
    copied = 0
    missing = []
    for mon in read_pokedex(export)["pokemon"]:
        if mon["front"]:
            continue
        stem = mon["token"].removeprefix("SPECIES_").lower()
        for gender in ("male", "female"):
            sprite = engine_sprites / stem / gender / "front.png"
            if is_battle_sheet(sprite):
                shutil.copyfile(sprite, folder / f"{stem}.png")
                copied += 1
                break
        else:
            missing.append(stem)
    print(f"Copied {copied} battle sprites. Missing {len(missing)}: {', '.join(missing) or 'none'}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fill missing Pokédex battle sprites from the build graphics")
    parser.add_argument("--source", type=Path, required=True, help="Reviewed guide export directory")
    parser.add_argument("--engine-sprites", type=Path, required=True, help="Build's data/graphics/sprites directory")
    args = parser.parse_args()
    copy_missing_battle_sprites(args.source, args.engine_sprites)
