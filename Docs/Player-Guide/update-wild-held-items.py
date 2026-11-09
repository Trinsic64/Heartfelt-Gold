"""Refresh wild held items in the reviewed guide export from Species.c.

The existing wild icon identifies form-specific species when the CSV display
name alone does not. Run this before build-standalone.py.
"""

import argparse
import csv
import hashlib
import json
import re
from pathlib import Path

from PIL import Image

WILD_FILES = ("Wild-Grass.csv", "Wild-Surfing-Fishing.csv", "Wild-Headbutt-Rock-Smash.csv")


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def held_items(path):
    source = path.read_text(encoding="utf-8")
    starts = list(re.finditer(r"(?m)^\s*\[SPECIES_([A-Z0-9_]+)\]\s*=\s*\{", source))
    items = {}
    for index, match in enumerate(starts):
        block = source[match.end():starts[index + 1].start() if index + 1 < len(starts) else len(source)]
        held = re.search(
            r"\.wildHeldItems\s*=\s*\{\s*\.common\s*=\s*(ITEM_[A-Z0-9_]+)\s*,"
            r"\s*\.rare\s*=\s*(ITEM_[A-Z0-9_]+)", block
        )
        if not held:
            raise ValueError(f"No wild held items for {match.group(1)}")
        items[match.group(1)] = held.groups()
    if len(items) != len(starts):
        raise ValueError("Duplicate species records")
    return items


def item_name(token):
    if token == "ITEM_NONE":
        return "No item"
    parts = token.removeprefix("ITEM_").split("_")
    return " ".join(part if part in {"HP", "PP", "TM", "XS", "XL", "X"} else part.title() for part in parts)


def species_token(row):
    token = row.get("speciesToken") or row.get("Species token")
    return token or Path(row.get("icon") or row["Pokémon icon"]).stem.upper()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--old-species", type=Path, required=True)
    parser.add_argument("--new-species", type=Path, required=True)
    parser.add_argument("--new-item-art", type=Path, required=True)
    parser.add_argument("--docs", type=Path, required=True)
    args = parser.parse_args()
    old = held_items(args.old_species)
    new = held_items(args.new_species)
    if old.keys() != new.keys():
        raise ValueError("Species sets differ")
    new_sha = sha256(args.new_species)
    used_sprites = set()
    missing_sprites = set()

    def sprite(token):
        if token == "ITEM_NONE":
            return ""
        name = item_name(token)
        slug = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
        source = args.new_item_art / f"{slug}.png"
        relative = Path("Sprites/Items") / source.name
        target = args.docs / relative
        if not source.is_file():
            missing_sprites.add(token)
            return ""
        if not target.is_file():
            target.parent.mkdir(parents=True, exist_ok=True)
            with Image.open(source) as image:
                if image.mode == "P" and "transparency" not in image.info:
                    rgba = image.convert("RGBA")
                    mask = Image.frombytes("L", image.size, image.tobytes())
                    rgba.putalpha(mask.point(lambda color: 0 if color == 0 else 255))
                    rgba.save(target)
                else:
                    image.convert("RGBA").save(target)
        used_sprites.add(relative.as_posix())
        return relative.as_posix()

    page = args.docs / "Heartfelt-Gold-Walkthrough.html"
    html = page.read_text(encoding="utf-8")
    match = re.search(r"window\.GUIDE_DATA=(\{.*?\});</script>", html)
    if not match:
        raise ValueError("Guide data not found")
    data = json.loads(match.group(1))
    changed_rows = 0
    for area in data["wild"]:
        for entry in area["entries"]:
            species = species_token(entry)
            if species not in old:
                raise ValueError(f"Unknown guide species: {species}")
            expected_old = tuple(map(item_name, old[species]))
            expected_new = tuple(map(item_name, new[species]))
            actual = (entry["common"], entry["rare"])
            if actual not in (expected_old, expected_new):
                raise ValueError(f"Guide held items differ from both sources: {area['name']} {species}: {actual}")
            if actual != expected_new:
                changed_rows += 1
            entry["common"], entry["rare"] = expected_new
            entry["commonSprite"] = sprite(new[species][0])
            entry["rareSprite"] = sprite(new[species][1])
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    html = html[:match.start(1)] + payload + html[match.end(1):]
    page.write_text(html, encoding="utf-8", newline="\n")

    csv_rows = 0
    for filename in WILD_FILES:
        path = args.docs / filename
        with path.open(newline="", encoding="utf-8-sig") as stream:
            rows = list(csv.DictReader(stream))
        for row in rows:
            species = species_token(row)
            if species not in new:
                raise ValueError(f"Unknown CSV species: {species}")
            row["Common held"] = item_name(new[species][0])
            row["Rare held"] = item_name(new[species][1])
            row["Common held icon"] = sprite(new[species][0])
            row["Rare held icon"] = sprite(new[species][1])
        fields = list(rows[0])
        with path.open("w", newline="", encoding="utf-8-sig") as stream:
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
        csv_rows += len(rows)
    if csv_rows != sum(len(area["entries"]) for area in data["wild"]):
        raise ValueError("HTML and CSV wild row counts differ")
    if sha256(args.new_species) != new_sha:
        raise ValueError("Species.c changed during export")
    print(f"Updated {changed_rows} of {csv_rows} wild rows; {len(used_sprites)} item sprites, {len(missing_sprites)} missing")
    if missing_sprites:
        print("Missing item sprites:", ", ".join(sorted(missing_sprites)))


if __name__ == "__main__":
    main()
