"""Check that the published guide, offline ZIP, and patch name the same release."""

import hashlib
import json
import csv
import base64
import re
import runpy
import zipfile
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
SITE = HERE / "site"
release = json.loads((HERE / "release.json").read_text(encoding="utf-8"))
version = release["version"]
assert release["tag"] == f"heartfelt-{version}"
assert release["patch"] == f"xDelta/Heartfelt-Gold-{version}-Patch.xdelta"

patch = ROOT / release["patch"]
with patch.open("rb") as stream:
    assert hashlib.file_digest(stream, "sha256").hexdigest() == release["patchSha256"]

assert json.loads((SITE / "release.json").read_text(encoding="utf-8")) == release
for page in ("index.html", "Rematch-Trainer-Guide.html"):
    html = (SITE / page).read_text(encoding="utf-8")
    assert f"POKÉMON HEARTFELT GOLD · PLAYER GUIDE · {version}" in html, page
    assert "Guide-App.js\"" not in html and "Guide-Style.css\"" not in html, page

species_file = ROOT / "HG-Engine/data/Species.c"
with species_file.open("rb") as stream:
    assert hashlib.file_digest(stream, "sha256").hexdigest() == release["heldItemSpeciesSha256"]
species_text = species_file.read_text(encoding="utf-8")
starts = list(re.finditer(r"(?m)^\s*\[SPECIES_([A-Z0-9_]+)\]\s*=\s*\{", species_text))
held = {}
species_blocks = {}
for index, match in enumerate(starts):
    block = species_text[match.end():starts[index + 1].start() if index + 1 < len(starts) else len(species_text)]
    species_blocks["SPECIES_" + match.group(1)] = block
    items = re.search(r"\.wildHeldItems\s*=\s*\{\s*\.common\s*=\s*(ITEM_[A-Z0-9_]+)\s*,"
                      r"\s*\.rare\s*=\s*(ITEM_[A-Z0-9_]+)", block)
    assert items, match.group(1)
    held[match.group(1)] = items.groups()

def item_name(token):
    if token == "ITEM_NONE":
        return "No item"
    return " ".join(part if part in {"HP", "PP", "TM", "XS", "XL", "X"} else part.title()
                    for part in token.removeprefix("ITEM_").split("_"))

main_html = (SITE / "index.html").read_text(encoding="utf-8")
guide_data = json.loads(re.search(r"window\.GUIDE_DATA=(\{.*?\});</script>", main_html).group(1))
html_wild = Counter()
for area in guide_data["wild"]:
    for entry in area["entries"]:
        species = entry.get("speciesToken") or Path(entry["icon"]).stem.upper()
        assert (entry["common"], entry["rare"]) == tuple(map(item_name, held[species])), species
        html_wild[(area["name"], entry["method"], entry["time"], entry["name"],
                   entry["min"], entry["max"], entry["common"], entry["rare"])] += 1
csv_wild = Counter()
for filename in ("Wild-Grass.csv", "Wild-Surfing-Fishing.csv", "Wild-Headbutt-Rock-Smash.csv"):
    with (SITE / filename).open(newline="", encoding="utf-8-sig") as stream:
        for row in csv.DictReader(stream):
            csv_wild[(row["Area"], row["Method"], row["Time"], row["Pokémon"],
                      row["Min level"], row["Max level"], row["Common held"], row["Rare held"])] += 1
assert html_wild == csv_wild

markdown = (ROOT / "Docs/Guides/Static-Encounter-Guide.md").read_text(encoding="utf-8")
markdown_statics = Counter()
for line in markdown.split("## v22 Test script audit", 1)[0].splitlines():
    if line.startswith("| **"):
        cells = [cell.strip().strip("*") for cell in line.split("|")[1:-1]]
        if len(cells) >= 4 and cells[0] != "Pokémon":
            markdown_statics[(cells[0], cells[1], cells[2])] += 1
html_statics = Counter((entry["name"], entry["level"], entry["area"]) for entry in guide_data["statics"])
with (SITE / "Static-Encounters.csv").open(newline="", encoding="utf-8-sig") as stream:
    csv_statics = Counter((row["Pokémon"], row["Level"], row["Area"]) for row in csv.DictReader(stream))
assert markdown_statics == html_statics == csv_statics


def normalized(value):
    return re.sub(r"[^a-z0-9]", "", value.casefold())


for relative, key in (
    ("HG-Engine/data/Trainers.c", "trainerSourceSha256"),
    ("HG-Engine/data/Encounters.c", "encounterSourceSha256"),
    ("HG-Engine/data/Evolutions.c", "evolutionSourceSha256"),
    ("HG-Engine/data/itemdata/itemdata.c", "itemDataSourceSha256"),
    ("HG-Engine/src/field/mart.c", "martSourceSha256"),
    ("HG-Engine/src/battle/mega.c", "megaSourceSha256"),
    ("HG-Engine/data/PokeFormDataTbl.c", "formTableSha256"),
):
    with (ROOT / relative).open("rb") as stream:
        assert hashlib.file_digest(stream, "sha256").hexdigest() == release[key], relative

trainer_text = (ROOT / "HG-Engine/data/Trainers.c").read_text(encoding="utf-8")
trainer_starts = list(re.finditer(r"(?m)^\s*\[(\d+)\]\s*=\s*\{", trainer_text))
trainer_blocks = {int(match.group(1)): trainer_text[match.end():trainer_starts[i + 1].start()
                  if i + 1 < len(trainer_starts) else len(trainer_text)]
                  for i, match in enumerate(trainer_starts)}
html_trainers = {t["id"]: t for t in guide_data["trainers"]}
csv_trainers = {}
with (SITE / "Trainers-Story-Order.csv").open(newline="", encoding="utf-8-sig") as stream:
    for row in csv.DictReader(stream):
        csv_trainers.setdefault(int(row["Trainer ID"]), []).append(row)
assert 0 not in html_trainers and 0 not in csv_trainers

# Both League runs are story chapters, each with its own bonus parties.
league_names = ("will", "koga", "bruno", "karen", "lance")
first_run = ((245, 746), (247, 747), (418, 748), (246, 749), (244, 750))
second_run = ((702, 759), (703, 760), (704, 761), (705, 762), (701, 763))
chapters = {chapter["number"]: chapter["label"] for chapter in guide_data["chapters"]}
assert "after 8 badges" in chapters[31] and "after 16 badges" in chapters[43]
assert chapters[44].endswith("Mt. Silver / Red")
groups = {group["id"]: index for index, group in enumerate(guide_data["trainerGroups"])}
assert groups["gym-42"] < groups["postleague-will"] < groups["postleague-lance"] < groups["stage-44"]
for name, first, second in zip(league_names, first_run, second_run):
    for ids, prefix, chapter in ((first, "league-", "31 "), (second, "postleague-", "43 ")):
        main_id, bonus_id = ids
        for trainer_id, is_bonus in ((main_id, False), (bonus_id, True)):
            trainer = html_trainers[trainer_id]
            rows = csv_trainers[trainer_id]
            assert trainer["group"] == prefix + name and trainer["stage"].startswith(chapter)
            assert trainer["bonus"] is is_bonus and len(rows) == len(trainer["team"]) == 6
            assert all(row["Story stage (approx.)"] == trainer["stage"] for row in rows)
            assert all(row["Battle kind"] == ("Bonus battle" if is_bonus else "Main / special battle")
                       for row in rows)

rematch_html = (SITE / "Rematch-Trainer-Guide.html").read_text(encoding="utf-8")
rematch_data = json.loads(re.search(r"window\.GUIDE_DATA=(\{.*?\});</script>", rematch_html).group(1))
rematch_ids = {trainer["id"] for trainer in rematch_data["trainers"]}
with (SITE / "Rematch-Trainers.csv").open(newline="", encoding="utf-8-sig") as stream:
    rematch_csv_ids = {int(row["Trainer ID"]) for row in csv.DictReader(stream)}
assert not ({main_id for main_id, _ in second_run} & (rematch_ids | rematch_csv_ids))
assert guide_data["counts"]["trainers"] == len(html_trainers)
assert guide_data["counts"]["rematches"] == rematch_data["counts"]["rematches"] == len(rematch_ids)

gym_groups = [group["id"] for group in guide_data["trainerGroups"]
              if group["id"].startswith("gym-")]
assert len(gym_groups) == 16
for group in gym_groups:
    members = [t for t in guide_data["trainers"] if t["group"] == group]
    ranks = [2 if t["bonus"] else 1 if t["major"] else 0 for t in members]
    assert ranks == sorted(ranks) and ranks.count(1) == ranks.count(2) == 1, group
    ids = [t["id"] for t in members]
    assert [trainer_id for trainer_id in csv_trainers if trainer_id in ids] == ids, group
assert main_html.count("gymOrder(a, b)") >= 2  # Walkthrough and Trainer tab share the rank.

mega_helpers = runpy.run_path(str(HERE / "add-trainer-mega-forms.py"))
reverse, stone_forms, stone_items, move_forms, mega_species = mega_helpers["read_tables"]()
normalize_mega = mega_helpers["normalize"]
mega_totals = Counter()
unresolved_stones = Counter()
for page_data, page_html in ((guide_data, main_html), (rematch_data, rematch_html)):
    sprite_match = re.search(r"window\.GUIDE_SPRITES=(\{.*?\});</script>", page_html)
    assert sprite_match
    embedded_sprites = json.loads(sprite_match.group(1))
    for trainer in page_data["trainers"]:
        for mon in trainer["team"]:
            raw_species = "SPECIES_" + Path(mon["icon"]).stem.upper()
            base, form_number = reverse.get(raw_species, (raw_species, 0))
            item = next((token for token in stone_items
                         if normalize_mega(mon["held"]) == normalize_mega(token.removeprefix("ITEM_"))), None)
            target = stone_forms.get((base, item, form_number)) if item else None
            if not target:
                for move in mon["moves"]:
                    target = move_forms.get((base, normalize_mega(move), form_number))
                    if target:
                        break
            if not target:
                assert "mega" not in mon, (trainer["id"], mon["name"])
                if item:
                    unresolved_stones[(raw_species, mon["held"])] += 1
                continue
            mega = mon["mega"]
            expected = mega_species[target]
            assert all(mega[key] == expected[key] for key in ("speciesToken", "name", "types", "ability"))
            stem = target.removeprefix("SPECIES_").lower()
            for kind, folder, key in (("Front", "TrainerMegaFront", "front"),
                                      ("ColorIcons", "TrainerMegaIcons", "icon")):
                path = f"Sprites/{folder}/{stem}.png"
                assert mega[key] == path and path in embedded_sprites
                vendor = HERE / "mega-sprites" / kind / f"{stem}.png"
                assert base64.b64decode(embedded_sprites[path].split(",", 1)[1]) == vendor.read_bytes()
            mega_totals[target] += 1
assert sum(mega_totals.values()) == 500 and len(mega_totals) == 88
assert unresolved_stones == Counter({("SPECIES_TATSUGIRI", "Tatsugirinite"): 4,
                                     ("SPECIES_FLOETTE", "Floettite"): 1})
assert "const shown = m.mega || m" in main_html and "const shown = m.mega || m" in rematch_html
assert not any("mega" in entry for area in guide_data["wild"] for entry in area["entries"])

hidden = dict(re.findall(r"\[(SPECIES_[A-Z0-9_]+)\s*\]\s*=\s*(ABILITY_[A-Z0-9_]+)",
                         (ROOT / "HG-Engine/data/HiddenAbilityTable.c").read_text(encoding="utf-8")))
changed_ids = set(release["changedTrainerPartyIds"]) - {0}
assert len(changed_ids) == 21
for trainer_id in changed_ids:
    block = trainer_blocks[trainer_id]
    fields = {field: re.findall(r"(?m)^\s*\." + field + r"\s*=\s*([^,\r\n]+)", block)
              for field in ("level", "species", "item", "abilitySlot")}
    moves = [re.findall(r"MOVE_[A-Z0-9_]+", line) for line in
             re.findall(r"(?m)^\s*\.moves\s*=\s*\{\s*([^}]+)\}", block)]
    team = html_trainers[trainer_id]["team"]
    csv_team = csv_trainers[trainer_id]
    assert all(len(values) == len(team) == len(csv_team) == 6 for values in (*fields.values(), moves)), trainer_id
    for index, (mon, row) in enumerate(zip(team, csv_team)):
        token = fields["species"][index].strip()
        item = fields["item"][index].strip()
        slot = fields["abilitySlot"][index].strip()
        assert Path(mon["icon"]).stem.upper() == token.removeprefix("SPECIES_")
        assert int(mon["level"]) == int(row["Level"]) == int(fields["level"][index])
        assert normalized(mon["name"]) == normalized(row["Pokémon"])
        expected_item = "" if item == "ITEM_NONE" else item.removeprefix("ITEM_")
        assert normalized(mon["held"]) == normalized(row["Held item"]) == normalized(expected_item)
        expected_moves = [move.removeprefix("MOVE_") for move in moves[index] if move != "MOVE_NONE"]
        assert [normalized(move) for move in mon["moves"]] == [normalized(move) for move in expected_moves], trainer_id
        assert [normalized(move) for move in row["Moves"].split("; ")] == [normalized(move) for move in expected_moves]
        expected_slot = {"TRAINER_POKEMON_ABILITY_1": "Slot 1", "TRAINER_POKEMON_ABILITY_2": "Slot 2",
                         "TRAINER_POKEMON_ABILITY_HIDDEN": "Hidden"}[slot]
        assert mon["abilitySlot"] == row["Ability slot"] == expected_slot
        abilities = re.search(r"\.abilities\s*=\s*\{\s*(ABILITY_\w+)\s*,\s*(ABILITY_\w+)\s*\}", species_blocks[token])
        assert abilities
        ability = hidden[token] if expected_slot == "Hidden" else abilities.group(2 if expected_slot == "Slot 2" else 1)
        assert normalized(mon["ability"]) == normalized(row["Ability"]) == normalized(ability.removeprefix("ABILITY_"))
        assert row["Pokémon icon"] == mon["icon"] and int(row["Party slot"]) == index + 1

mart_text = (ROOT / "HG-Engine/src/field/mart.c").read_text(encoding="utf-8")
cherrygrove = mart_text.split("sCherrygroveCityMart[] = {", 1)[1].split("};", 1)[0]
assert "ITEM_CHERISH_BALL" in cherrygrove and "ITEM_NEST_BALL" not in cherrygrove
with (SITE / "Marts-and-Department-Stores.csv").open(newline="", encoding="utf-8-sig") as stream:
    shops_csv = list(csv.DictReader(stream))
assert len([row for row in shops_csv if row["Shop"] == "Cherrygrove City Mart" and row["Item"] == "Cherish Ball"]) == 1
assert len([item for shop in guide_data["shops"] if shop["name"] == "Cherrygrove City Mart"
            for item in shop["items"] if item["name"] == "Cherish Ball"]) == 1

mart_helpers = runpy.run_path(str(HERE / "add-mart-prices.py"))
item_prices = mart_helpers["read_prices"]()
item_token = mart_helpers["item_token"]
html_shop_rows = Counter()
for shop in guide_data["shops"]:
    for item in shop["items"]:
        assert item["price"] == item_prices[item_token(item["sprite"])]
        html_shop_rows[(shop["name"], shop["floor"], item["name"], str(item["price"]),
                        item["sprite"], item["badges"])] += 1
csv_shop_rows = Counter((row["Shop"], row["Floor / state"], row["Item"], row["Price"],
                         row["Item sprite"], row["Badges required"]) for row in shops_csv)
assert html_shop_rows == csv_shop_rows and sum(html_shop_rows.values()) == 1065
assert len({shop["name"] for shop in guide_data["shops"]}) == 21
shop_tabs = Counter((shop["name"], shop["floor"]
                     if "Department Store" in shop["name"] else "") for shop in guide_data["shops"])
assert len(shop_tabs) == 30
shared_floors = {"2F lower counter", "2F upper counter", "3F", "4F"}
assert {floor for name, floor in shop_tabs if name == "Goldenrod Department Store"} == shared_floors | {"5F"}
assert {floor for name, floor in shop_tabs if name == "Celadon Department Store"} == shared_floors | {"5F left counter", "5F right counter"}
assert "shop-table .shop-icon{width:36px" in main_html

pokedex = guide_data["pokedex"]
expected_dex = runpy.run_path(str(HERE / "pokedex-data.py"))["read_pokedex"]()
assert [{k: v for k, v in mon.items() if k != "icon"} for mon in pokedex["pokemon"]] == expected_dex["pokemon"]
assert pokedex["machineMoves"] == expected_dex["machineMoves"]
for shop, floor, item, *_ in html_shop_rows:
    if re.fullmatch(r"(?:TM|HM|TR)\d+(?:_[A-Z]+)?", item):
        assert item in pokedex["machineMoves"], (shop, floor, item)
main_sprites = json.loads(re.search(r"window\.GUIDE_SPRITES=(\{.*?\});</script>", main_html).group(1))
assert all(not mon["icon"] or mon["icon"] in main_sprites for mon in pokedex["pokemon"])
assert "pokedex" not in rematch_data

evo_text = (ROOT / "HG-Engine/data/Evolutions.c").read_text(encoding="utf-8")
for source, result in (("FRILLISH", "SPECIES_JELLICENT"),
                       ("FRILLISH_FEMALE", "MON_WITH_FORM(SPECIES_JELLICENT, 1)")):
    block = evo_text.split(f"[SPECIES_{source}] = {{", 1)[1].split("[SPECIES_", 1)[0]
    assert f"{{ EVO_LEVEL, 40, {result} }}" in block
with (SITE / "Evolution-Guide.csv").open(newline="", encoding="utf-8-sig") as stream:
    frillish_csv = [row for row in csv.DictReader(stream) if row["From"] in {"Frillish", "Frillish Female"}]
assert len(frillish_csv) == 2 and all(row["Requirement"] == "Lv 40" and row["Engine method"] == "EVO_LEVEL"
                                   for row in frillish_csv)
assert len([e for e in guide_data["evos"] if e["from"] in {"Frillish", "Frillish Female"}
            and e["requirement"] == "Lv 40" and e["method"] == "EVO_LEVEL"]) == 2

archive = SITE / "Heartfelt-Gold-Player-Guide-Offline.zip"
with archive.open("rb") as stream:
    guide_hash = hashlib.file_digest(stream, "sha256").hexdigest()
with zipfile.ZipFile(archive) as bundle:
    assert bundle.testzip() is None
    for path in SITE.iterdir():
        if path.is_file() and path != archive:
            assert bundle.read(path.name) == path.read_bytes(), path.name

checksum_entry = f"{release['patchSha256']} *{release['patch']}"
assert checksum_entry in (ROOT / "checksums.sha256").read_text(encoding="utf-8")
asset_checksums = (ROOT / f"RELEASE-CHECKSUMS-HEARTFELT-{version}.sha256").read_text(encoding="utf-8")
assert f"{release['patchSha256']} *{patch.name}" in asset_checksums
assert f"{guide_hash} *{archive.name}" in asset_checksums
assert version in (ROOT / "README.md").read_text(encoding="utf-8")
assert (ROOT / f"RELEASE-NOTES-HEARTFELT-{version}.md").is_file()
print(f"PASS: {version} patch, HGEFE teams, {sum(mega_totals.values())} Mega displays, held items, "
      "1,065 Mart prices, Pokédex, machine moves, evolutions, statics, site, ZIP, checksums, and notes agree")
