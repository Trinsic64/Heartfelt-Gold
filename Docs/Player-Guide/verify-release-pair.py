"""Check that the published guide, offline ZIP, and patch name the same release."""

import hashlib
import json
import csv
import re
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
for index, match in enumerate(starts):
    block = species_text[match.end():starts[index + 1].start() if index + 1 < len(starts) else len(species_text)]
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
print(f"PASS: {version} patch, held items, static levels, site, ZIP, checksums, and notes agree")
