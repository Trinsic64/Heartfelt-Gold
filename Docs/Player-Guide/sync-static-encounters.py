"""Align the reviewed static CSV and HTML export with the Markdown guide."""

import argparse
import csv
import json
import re
from pathlib import Path

from PIL import Image

ADDED_BINDINGS = {
    "Spectrier": ("0252", 22),
    "Glastrier": ("0257", 26),
    "Phione": ("0260", 20),
}
SOURCE_URL = "https://github.com/Trinsic64/Heartfelt-Gold/blob/main/Docs/Guides/Static-Encounter-Guide.md"


def markdown_rows(path):
    text = re.split(r"## v22 [Tt]est script audit", path.read_text(encoding="utf-8"), maxsplit=1)[0]
    rows = []
    for line in text.splitlines():
        if line.startswith("| **"):
            cells = [cell.strip().strip("*") for cell in line.split("|")[1:-1]]
            if len(cells) >= 4 and cells[0] != "Pokémon":
                rows.append({"name": cells[0], "level": cells[1], "area": cells[2], "parent": cells[3]})
    if not rows or len({(row["name"], row["area"]) for row in rows}) != len(rows):
        raise ValueError("Missing or duplicate static encounter rows in Markdown")
    return rows


def sprite(name, docs, root):
    source = root / name.lower() / "icon.png"
    if not source.is_file():
        raise FileNotFoundError(source)
    relative = Path("Sprites/ColorIcons") / f"{name.lower()}.png"
    target = docs / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(source) as image:
        if image.mode == "P" and "transparency" not in image.info:
            rgba = image.convert("RGBA")
            mask = Image.frombytes("L", image.size, image.tobytes())
            rgba.putalpha(mask.point(lambda color: 0 if color == 0 else 255))
            rgba.save(target)
        else:
            image.convert("RGBA").save(target)
    return relative.as_posix()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--markdown", type=Path, required=True)
    parser.add_argument("--docs", type=Path, required=True)
    parser.add_argument("--sprite-root", type=Path, required=True)
    args = parser.parse_args()
    reviewed = markdown_rows(args.markdown)
    csv_path = args.docs / "Static-Encounters.csv"
    with csv_path.open(newline="", encoding="utf-8-sig") as stream:
        current = list(csv.DictReader(stream))
    by_key = {(row["Pokémon"], row["Area"]): row for row in current}
    if len(by_key) != len(current):
        raise ValueError("Duplicate static CSV rows")
    desired_keys = {(row["name"], row["area"]) for row in reviewed}
    extra = set(by_key) - desired_keys
    if extra not in (set(), {("Victini", "Union Cave")}):
        raise ValueError(f"Unexpected static CSV entries absent from Markdown: {extra}")

    rows = []
    added = 0
    for entry in reviewed:
        name, level, area = entry["name"], entry["level"], entry["area"]
        key = (name, area)
        if key in by_key:
            row = dict(by_key[key])
            row["Level"] = level
        else:
            if name not in ADDED_BINDINGS or not area.startswith("Route "):
                raise ValueError(f"Unreviewed added encounter: {key}")
            bank, _ = ADDED_BINDINGS[name]
            row = {
                "Pokémon": name, "Level": level, "Area": area, "Map header": "",
                "Script bank": bank, "Pokémon icon": sprite(name, args.docs, args.sprite_root),
                "Notes": "Event object bound; unlock not verified", "Source": SOURCE_URL,
                "Parent area": area, "Parent link": "Same map; event object bound",
            }
            added += 1
        rows.append(row)

    fields = list(current[0])
    with csv_path.open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    page = args.docs / "Heartfelt-Gold-Walkthrough.html"
    html = page.read_text(encoding="utf-8")
    match = re.search(r"window\.GUIDE_DATA=(\{.*?\});</script>", html)
    if not match:
        raise ValueError("Guide data not found")
    data = json.loads(match.group(1))
    existing = {(entry["name"], entry["area"]): entry for entry in data["statics"]}
    if set(existing) != set(by_key):
        raise ValueError("HTML and static CSV entries differ")
    statics = []
    for row in rows:
        key = (row["Pokémon"], row["Area"])
        if key in existing:
            entry = dict(existing[key])
            entry["level"] = row["Level"]
        else:
            bank, chapter = ADDED_BINDINGS[row["Pokémon"]]
            entry = {
                "name": row["Pokémon"], "level": row["Level"], "area": row["Area"],
                "parent": row["Parent area"], "parentLink": row["Parent link"],
                "header": "", "bank": bank, "icon": row["Pokémon icon"], "chapter": chapter,
            }
        statics.append(entry)
    data["statics"] = statics
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    page.write_text(html[:match.start(1)] + payload + html[match.end(1):], encoding="utf-8", newline="\n")
    print(f"Aligned {len(rows)} static encounters with Markdown; added {added}, excluded unbound Union Cave Victini: {bool(extra)}")


if __name__ == "__main__":
    main()
