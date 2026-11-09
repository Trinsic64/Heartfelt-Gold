"""Add in-battle Mega form display data to trainer HTML only.

Reads the build's Mega Stone, form, and species tables. Base trainer party data
and the trainer CSV remain unchanged because the ROM stores the pre-Mega form.
Sprites are copied from the build graphics to versioned guide assets.
"""

import argparse
import json
import re
import shutil
from collections import Counter
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
ASSETS = HERE / "mega-sprites"
DATA_PATTERN = re.compile(r"window\.GUIDE_DATA=(\{.*?\});</script>")
SPECIES_PATTERN = re.compile(r"(?m)^\s*\[(SPECIES_[A-Z0-9_]+)\]\s*=\s*\{")
KNOWN_NON_MEGA_STONES = {
    ("SPECIES_TATSUGIRI", "Tatsugirinite"),
    ("SPECIES_FLOETTE", "Floettite"),
}


def field(block, name):
    match = re.search(r"\." + name + r"\s*=\s*([A-Z0-9_]+)", block)
    if not match:
        raise ValueError(f"Missing {name}: {block[:100]}")
    return match.group(1)


def normalize(value):
    return re.sub(r"[^A-Z0-9]", "", value.upper())


def display(token, prefix):
    return " ".join(word.title() for word in token.removeprefix(prefix).split("_"))


def read_tables():
    mega_text = (ROOT / "HG-Engine/src/battle/mega.c").read_text(encoding="utf-8")
    form_text = (ROOT / "HG-Engine/data/PokeFormDataTbl.c").read_text(encoding="utf-8")
    species_text = (ROOT / "HG-Engine/data/Species.c").read_text(encoding="utf-8")
    mega_text = re.sub(r"/\*.*?\*/|//[^\n]*", "", mega_text, flags=re.S)
    table = mega_text.split("sMegaTable[] = {", 1)[1].split("};", 1)[0]
    move_table = mega_text.split("sMegaMoveTable[] = {", 1)[1].split("};", 1)[0]

    forms = {}
    reverse = {}
    for match in re.finditer(r"\[(SPECIES_[A-Z0-9_]+)\]\s*=\s*\{([^{}]*)\}", form_text):
        base = match.group(1)
        members = re.findall(r"SPECIES_[A-Z0-9_]+", match.group(2))
        forms[base] = members
        for index, member in enumerate(members, 1):
            reverse[member] = (base, index)

    stone_forms = {}
    stone_items = set()
    for match in re.finditer(r"\{([^{}]*\.monindex[^{}]*)\}", table):
        block = match.group(1)
        base, item = field(block, "monindex"), field(block, "itemindex")
        target, base_form = int(field(block, "targetForm")), int(field(block, "baseForm"))
        stone_items.add(item)
        if target > len(forms.get(base, [])):
            # The source also lists some unused variants without a form-table entry.
            continue
        target_species = forms[base][target - 1]
        if not target_species.startswith("SPECIES_MEGA_"):
            # A few configured stones currently point at a non-Mega form.
            continue
        key = (base, item, base_form)
        if key in stone_forms:
            assert stone_forms[key] == target_species
        stone_forms[key] = target_species

    move_forms = {}
    for match in re.finditer(r"\{([^{}]*\.monindex[^{}]*)\}", move_table):
        block = match.group(1)
        base, move = field(block, "monindex"), field(block, "moveindex")
        target, base_form = int(field(block, "targetForm")), int(field(block, "baseForm"))
        move_forms[(base, normalize(move.removeprefix("MOVE_")), base_form)] = forms[base][target - 1]

    starts = list(SPECIES_PATTERN.finditer(species_text))
    species = {}
    for i, match in enumerate(starts):
        if not match.group(1).startswith("SPECIES_MEGA_"):
            continue
        block = species_text[match.end():starts[i + 1].start() if i + 1 < len(starts) else len(species_text)]
        types = re.search(r"\.types\s*=\s*\{\s*(TYPE_[A-Z0-9_]+)\s*,\s*(TYPE_[A-Z0-9_]+)\s*\}", block)
        abilities = re.search(r"\.abilities\s*=\s*\{\s*(ABILITY_[A-Z0-9_]+)\s*,\s*(ABILITY_[A-Z0-9_]+)\s*\}", block)
        assert types and abilities and abilities.group(1) == abilities.group(2), match.group(1)
        species[match.group(1)] = {
            "speciesToken": match.group(1),
            "name": display(match.group(1), "SPECIES_"),
            "types": list(dict.fromkeys(display(t, "TYPE_") for t in types.groups())),
            "ability": display(abilities.group(1), "ABILITY_"),
        }
    assert len(species) == 97
    return reverse, stone_forms, stone_items, move_forms, species


def copy_sprite(token, source, export):
    stem = token.removeprefix("SPECIES_").lower()
    for kind, folder, original in (("Front", "TrainerMegaFront", source / stem / "male/front.png"),
                                   ("ColorIcons", "TrainerMegaIcons", source / stem / "icon.png")):
        stored = ASSETS / kind / f"{stem}.png"
        stored.parent.mkdir(parents=True, exist_ok=True)
        if original.is_file():
            if not stored.is_file() or stored.read_bytes() != original.read_bytes():
                shutil.copyfile(original, stored)
        if not stored.is_file():
            raise FileNotFoundError(f"Missing Mega sprite: {original}")
        destination = export / "Sprites" / folder / stored.name
        destination.parent.mkdir(parents=True, exist_ok=True)
        if not destination.is_file() or destination.read_bytes() != stored.read_bytes():
            shutil.copyfile(stored, destination)
    return f"Sprites/TrainerMegaFront/{stem}.png", f"Sprites/TrainerMegaIcons/{stem}.png"


def update_page(path, reverse, stone_forms, stone_items, move_forms, species, sprite_source, export):
    html = path.read_text(encoding="utf-8")
    match = DATA_PATTERN.search(html)
    if not match:
        raise ValueError(f"Guide data not found: {path}")
    data = json.loads(match.group(1))
    counts = Counter()
    misses = []
    for trainer in data["trainers"]:
        for mon in trainer["team"]:
            original = "SPECIES_" + Path(mon["icon"]).stem.upper()
            base, form_number = reverse.get(original, (original, 0))
            item = next((token for token in stone_items
                         if normalize(mon["held"]) == normalize(token.removeprefix("ITEM_"))), None)
            target = stone_forms.get((base, item, form_number)) if item else None
            trigger = mon["held"] if target else ""
            if not target:
                for move in mon["moves"]:
                    key = (base, normalize(move), form_number)
                    if key in move_forms:
                        target = move_forms[key]
                        trigger = move
                        break
            if item and not target:
                if (original, mon["held"]) not in KNOWN_NON_MEGA_STONES:
                    raise ValueError(f"Unexpected unresolved Mega Stone: trainer {trainer['id']}, "
                                     f"{original}, {mon['held']}")
                misses.append((trainer["id"], mon["name"], mon["held"], original))
            if target:
                front, icon = copy_sprite(target, sprite_source, export)
                mon["mega"] = {**species[target], "front": front, "icon": icon,
                               "trigger": trigger}
                counts[target] += 1
            else:
                mon.pop("mega", None)
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    path.write_text(html[:match.start(1)] + payload + html[match.end(1):],
                    encoding="utf-8", newline="\n")
    return counts, misses


def main(export, sprite_source):
    reverse, stone_forms, stone_items, move_forms, species = read_tables()
    totals = Counter()
    misses = []
    for name in ("Heartfelt-Gold-Walkthrough.html", "Rematch-Trainer-Guide.html"):
        counts, unresolved = update_page(export / name, reverse, stone_forms, stone_items,
                                         move_forms, species, sprite_source, export)
        totals.update(counts)
        misses.extend(unresolved)
    preview = export / "Heartfelt-Gold-v23-Guide-Preview.html"
    if preview.exists():
        preview.write_bytes((export / "Heartfelt-Gold-Walkthrough.html").read_bytes())
    print(f"Mega display: {sum(totals.values())} trainer Pokémon, {len(totals)} distinct forms")
    print(f"Stone holders without an engine Mega form: {misses}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--engine-sprites", type=Path,
                        default=Path("__engine_sprites_not_provided__"),
                        help="Build graphics sprite directory; optional when all forms are vendored")
    args = parser.parse_args()
    main(args.source, args.engine_sprites)
