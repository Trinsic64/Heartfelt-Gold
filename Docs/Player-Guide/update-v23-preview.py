"""Prepare local v23 guide CSV/HTML from the verified HGEFE build.

This updates the reviewed export in --docs. It intentionally leaves the
published v1.0.11 site and release manifest alone until a matching patch
is ready to publish.
"""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
import re
import shutil
import sys
import zipfile


NAME_OVERRIDES = {
    "SPECIES_FLETCHINDER": "Fletchinder",
    "SPECIES_CORVISQUIRE": "Corvisquire",
    "SPECIES_ROARING_MOON": "Roaring Moon",
    "SPECIES_IRON_JUGULIS": "Iron Jugulis",
    "SPECIES_FLUTTER_MANE": "Flutter Mane",
    "SPECIES_BASCULEGION": "Basculegion",
    "SPECIES_IRON_VALIANT": "Iron Valiant",
    "SPECIES_SQUAWKABILLY": "Squawkabilly",
    "SPECIES_TAUROS_COMBAT": "Tauros (Combat Breed)",
    "SPECIES_TAUROS_BLAZE": "Tauros (Blaze Breed)",
    "SPECIES_NINETALES_ALOLAN": "Alolan Ninetales",
    "SPECIES_MAROWAK_ALOLAN": "Alolan Marowak",
    "SPECIES_SANDY_SHOCKS": "Sandy Shocks",
}


def rows(path: Path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader), reader.fieldnames


def write_rows(path: Path, entries, fields):
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(entries)


def blocks(source: str):
    found = list(re.finditer(r"(?m)^\s*\[(SPECIES_[A-Z0-9_]+)\]\s*=\s*\{", source))
    return {match.group(1): source[match.end():found[i + 1].start() if i + 1 < len(found) else len(source)]
            for i, match in enumerate(found)}


def friendly(token: str):
    return token.removeprefix("ABILITY_").replace("_", " ").title()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--docs", type=Path, required=True)
    parser.add_argument("--engine", type=Path, required=True)
    parser.add_argument("--catalog", type=Path, required=True, help="Data/Pokemon directory")
    parser.add_argument("--parsed-trainers", type=Path, required=True, help="HGEFE parseTrainersC JSON export")
    parser.add_argument("--validation", type=Path, required=True, help="v23 build validation JSON")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    docs, engine = args.docs, args.engine
    changed = json.loads(args.validation.read_text(encoding="utf-8"))["changedTrainerPartyIdsVersusV1_0_11"]
    parsed = {row["id"]: row for row in json.loads(args.parsed_trainers.read_text(encoding="utf-8"))}
    assert set(changed) == set(parsed), "HGEFE export does not cover all changed compiled trainer IDs"
    trainer_source = (engine / "data/Trainers.c").read_text(encoding="utf-8")
    for trainer in parsed.values():
        assert trainer["sourceBlock"] in trainer_source, f"Trainer {trainer['id']} changed after export"

    species_blocks = blocks((engine / "data/Species.c").read_text(encoding="utf-8"))
    hidden = dict(re.findall(r"\[(SPECIES_[A-Z0-9_]+)\s*\]\s*=\s*(ABILITY_[A-Z0-9_]+)",
                             (engine / "data/HiddenAbilityTable.c").read_text(encoding="utf-8")))
    species_rows, _ = rows(args.catalog / "Pokemon-Data.csv")
    species_names = {row["Species ID"]: row["Pokemon Name"] for row in species_rows}
    move_rows, _ = rows(args.catalog / "Move-Data.csv")
    move_names = {row["Move ID"]: row["Name"] for row in move_rows}
    item_rows, _ = rows(args.catalog / "Item-Data.csv")
    item_names = {row["Item ID"]: row["Name"] for row in item_rows}

    def member(raw):
        token = raw["species"]
        body = species_blocks[token]
        types_match = re.search(r"\.types\s*=\s*\{\s*(TYPE_\w+)\s*,\s*(TYPE_\w+)\s*\}", body)
        abilities_match = re.search(r"\.abilities\s*=\s*\{\s*(ABILITY_\w+)\s*,\s*(ABILITY_\w+)\s*\}", body)
        assert types_match and abilities_match, f"Missing species data: {token}"
        slot = raw["abilitySlot"]
        slot_names = {"TRAINER_POKEMON_ABILITY_1": "Slot 1", "TRAINER_POKEMON_ABILITY_2": "Slot 2",
                      "TRAINER_POKEMON_ABILITY_HIDDEN": "Hidden"}
        assert slot in slot_names, f"Unknown ability slot: {slot}"
        ability = raw["ability"] if raw["ability"] != "ABILITY_NONE" else (
            hidden[token] if slot_names[slot] == "Hidden" else abilities_match.group(2 if slot_names[slot] == "Slot 2" else 1))
        assert ability != "ABILITY_NONE", f"Missing ability: {token}"
        type_names = [value.removeprefix("TYPE_").title() for value in types_match.groups()]
        if type_names[0] == type_names[1]:
            type_names.pop()
        held = "" if raw["item"] == "ITEM_NONE" else item_names[raw["item"]]
        moves = [move_names[value] for value in raw["moves"] if value != "MOVE_NONE"]
        slug = token.removeprefix("SPECIES_").lower()
        icon = f"Sprites/ColorIcons/{slug}.png"
        front = f"Sprites/Front/{slug}.png"
        held_sprite = f"Sprites/Items/{raw['item'].removeprefix('ITEM_').lower()}.png" if held else ""
        for image in (icon, front, held_sprite):
            if image and not (docs / image).is_file():
                raise FileNotFoundError(docs / image)
        return {"name": NAME_OVERRIDES.get(token, species_names.get(token, token.removeprefix("SPECIES_").replace("_", " ").title())),
                "level": str(raw["level"]), "icon": icon, "front": front,
                "held": held, "heldSprite": held_sprite, "ability": friendly(ability),
                "abilitySlot": slot_names[slot], "moves": moves, "types": type_names}

    team_by_id = {id: [member(raw) for raw in trainer["party"]] for id, trainer in parsed.items() if id != 0}
    trainer_csv = docs / "Trainers-Story-Order.csv"
    csv_rows, csv_fields = rows(trainer_csv)
    old_by_id = {}
    for row in csv_rows:
        old_by_id.setdefault(int(row["Trainer ID"]), []).append(row)
    assert all(id in old_by_id for id in changed if id != 0)
    assert all(len(old_by_id[id]) == len(team_by_id[id]) for id in team_by_id)
    new_csv = []
    written = set()
    for row in csv_rows:
        id = int(row["Trainer ID"])
        if id == 0:
            continue  # Trainer 0 is an internal dummy, not a player battle.
        if id not in team_by_id:
            new_csv.append(row)
        elif id not in written:
            base = old_by_id[id][0]
            for slot, mon in enumerate(team_by_id[id], 1):
                new_csv.append({**base, "Party slot": str(slot), "Pokémon": mon["name"],
                                "Level": mon["level"], "Held item": mon["held"],
                                "Moves": "; ".join(mon["moves"]), "Pokémon icon": mon["icon"],
                                "Ability": mon["ability"], "Ability slot": mon["abilitySlot"]})
            written.add(id)
    assert written == set(team_by_id)

    mart_csv = docs / "Marts-and-Department-Stores.csv"
    marts, mart_fields = rows(mart_csv)
    mart_rows = [r for r in marts if r["Shop"] == "Cherrygrove City Mart" and r["Item"] in ("Nest Ball", "Cherish Ball")]
    assert len(mart_rows) == 1
    mart_rows[0]["Item"] = "Cherish Ball"
    mart_rows[0]["Item sprite"] = "Sprites/Items/cherish_ball.png"
    assert (docs / mart_rows[0]["Item sprite"]).is_file()

    evo_csv = docs / "Evolution-Guide.csv"
    evos, evo_fields = rows(evo_csv)
    frillish = [r for r in evos if r["From"] in ("Frillish", "Frillish Female") and "Jellicent" in r["Evolves into"]]
    assert len(frillish) == 2
    for row in frillish:
        row["Requirement"] = "Lv 40"
        row["Engine method"] = "EVO_LEVEL"

    main_html = docs / "Heartfelt-Gold-Walkthrough.html"
    html = main_html.read_text(encoding="utf-8")
    match = re.search(r"window\.GUIDE_DATA=(\{.*?\});</script>", html)
    assert match
    data = json.loads(match.group(1))
    html_ids = {t["id"] for t in data["trainers"]}
    assert set(changed) <= html_ids | {0}
    data["trainers"] = [({**t, "team": team_by_id[t["id"]]} if t["id"] in team_by_id else t)
                        for t in data["trainers"] if t["id"] != 0]
    data["counts"]["trainers"] = len(data["trainers"])
    shops = [s for s in data["shops"] if s["name"] == "Cherrygrove City Mart"]
    assert len(shops) == 1
    stock = [item for item in shops[0]["items"] if item["name"] in ("Nest Ball", "Cherish Ball")]
    assert len(stock) == 1
    stock[0]["name"] = "Cherish Ball"
    stock[0]["sprite"] = "Sprites/Items/cherish_ball.png"
    html_evos = [e for e in data["evos"] if e["from"] in ("Frillish", "Frillish Female") and "Jellicent" in e["to"]]
    assert len(html_evos) == 2
    for evo in html_evos:
        evo["requirement"] = "Lv 40"
        evo["method"] = "EVO_LEVEL"
    new_html = html[:match.start(1)] + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + html[match.end(1):]

    print(f"V23 preview: {len(team_by_id)} player-facing trainer parties, {len(new_csv)} trainer CSV rows, "
          "one mart item, two evolution rules, and the dummy Trainer 0 removed.")
    if not args.apply:
        print("Dry run. Pass --apply to write the local guide export.")
        return
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup = docs / ".codex-backups" / f"v23-guide-{stamp}"
    backup.mkdir(parents=True, exist_ok=False)
    for path in (trainer_csv, mart_csv, evo_csv, main_html):
        shutil.copy2(path, backup / path.name)
    write_rows(trainer_csv, new_csv, csv_fields)
    write_rows(mart_csv, marts, mart_fields)
    write_rows(evo_csv, evos, evo_fields)
    main_html.write_text(new_html, encoding="utf-8", newline="\n")
    preview = new_html.replace("<title>Heartfelt Gold Walkthrough</title>",
                               "<title>Heartfelt Gold Walkthrough · v23 preview</title>")
    preview = preview.replace("POKÉMON HEARTFELT GOLD · PLAYER GUIDE",
                              "POKÉMON HEARTFELT GOLD · PLAYER GUIDE · v23 preview", 1)
    (docs / "Heartfelt-Gold-v23-Guide-Preview.html").write_text(preview, encoding="utf-8", newline="\n")
    for path in (trainer_csv, mart_csv, evo_csv):
        shutil.copy2(path, docs / (path.stem + "-v23-Preview.csv"))
    (docs / "V23-PREVIEW-README.txt").write_text(
        "V23 guide preview from the HGEFE-synced build. The published v1.0.11 guide and patch remain paired.\n"
        "Open Heartfelt-Gold-v23-Guide-Preview.html from this Docs folder; keep Guide-App.js, Guide-Style.css, and Sprites beside it.\n"
        f"Built ROM SHA-256: {json.loads(args.validation.read_text(encoding='utf-8'))['outputSha256']}\n",
        encoding="utf-8")
    preview_dir = docs / "v23-Standalone-Preview"
    preview_dir.mkdir(exist_ok=True)
    bundler_path = Path(__file__).with_name("build-standalone.py")
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location("guide_bundler", bundler_path)
    assert spec and spec.loader
    bundler = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bundler)
    bundler.SITE = preview_dir
    css = (docs / "Guide-Style.css").read_text(encoding="utf-8")
    script = bundler.bundled_script(docs)
    for input_name, output_name in bundler.PAGES:
        bundler.build_page(docs, input_name, output_name, script, css, "v23 preview")
    for path in docs.iterdir():
        if path.is_file() and path.suffix.lower() == ".csv" and not path.stem.endswith("-v23-Preview"):
            shutil.copy2(path, preview_dir / path.name)
    audit_notes = docs / "Release-v22-Item-Audit.md"
    if audit_notes.is_file():
        shutil.copy2(audit_notes, preview_dir / audit_notes.name)
    (preview_dir / "START-HERE.txt").write_text(
        "V23 build guide preview. Open index.html; the pages work offline and include their sprites.\n"
        "This is a review copy, not the published v1.0.11 player guide.\n"
        f"Built ROM SHA-256: {json.loads(args.validation.read_text(encoding='utf-8'))['outputSha256']}\n",
        encoding="utf-8")
    (preview_dir / "README-CSV-Review.md").write_text(
        "# Heartfelt Gold v23 build preview\n\n"
        "Trainer teams, Cherrygrove Mart stock, and Frillish evolution rules were refreshed from "
        "the HGEFE source compiled into the v23 build. The 21 player-facing changed trainer parties "
        "are included in story order; bonus trainers remain with their story chapter and rematches "
        "stay on the separate page. Trainer 0 is an internal dummy and is omitted.\n\n"
        "The Diglett's Cave matrix and map archive match the v23 input ROM byte for byte. "
        "The wild encounter, held-item, static encounter, and item placement tables have no new "
        "source changes in this preview. The static levels remain the reviewed v22 values. "
        "Individual rows have not all been checked in gameplay.\n",
        encoding="utf-8")
    archive = preview_dir / "Heartfelt-Gold-v23-Guide-Preview-Offline.zip"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
        for path in sorted(preview_dir.iterdir()):
            if path.is_file() and path != archive:
                info = zipfile.ZipInfo(path.name, date_time=(1980, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o644 << 16
                bundle.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    with zipfile.ZipFile(archive) as bundle:
        assert bundle.testzip() is None
        assert bundle.read("index.html") == (preview_dir / "index.html").read_bytes()
    print(f"Updated local guide export; previous files: {backup}")
    print(f"Offline review bundle: {archive}")


if __name__ == "__main__":
    main()
