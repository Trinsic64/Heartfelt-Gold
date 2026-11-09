"""Fill shop prices from the same itemdata.c snapshot as the v1.0.12 build.

Updates the reviewed HTML data and Mart CSV. Prices are stored as integers in
the CSV and formatted with the Pokédollar symbol by Guide-App.js.
"""

import argparse
import csv
import json
import re
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
DATA_PATTERN = re.compile(r"window\.GUIDE_DATA=(\{.*?\});</script>")
ITEM_PATTERN = re.compile(r"(?m)^\[(ITEM_[A-Z0-9_]+)\]\s*=\s*\{")


def read_prices():
    text = (ROOT / "HG-Engine/data/itemdata/itemdata.c").read_text(encoding="utf-8")
    starts = list(ITEM_PATTERN.finditer(text))
    prices = {}
    for index, match in enumerate(starts):
        block = text[match.end():starts[index + 1].start() if index + 1 < len(starts) else len(text)]
        macro = re.search(r"\bITEM_PRICE\s*\(\s*(\d+)\s*\)", block)
        if macro:
            price = int(macro.group(1))
        else:
            low = re.search(r"\.price\s*=\s*(\d+)", block)
            high = re.search(r"\.price_high\s*=\s*(\d+)", block)
            if not low:
                raise ValueError(f"No price field for {match.group(1)}")
            price = int(low.group(1)) + (int(high.group(1)) << 16 if high else 0)
        prices[match.group(1)] = price
    return prices


def item_token(sprite):
    return "ITEM_" + Path(sprite).stem.upper()


def update(source):
    prices = read_prices()
    page = source / "Heartfelt-Gold-Walkthrough.html"
    html = page.read_text(encoding="utf-8")
    match = DATA_PATTERN.search(html)
    if not match:
        raise ValueError(f"Guide data not found: {page}")
    data = json.loads(match.group(1))
    missing = set()
    priced = 0
    for shop in data["shops"]:
        for item in shop["items"]:
            token = item_token(item["sprite"])
            if token not in prices:
                missing.add((item["name"], token))
                continue
            item["price"] = prices[token]
            priced += 1
    if missing:
        raise ValueError(f"Shop items without source prices: {sorted(missing)}")
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    page.write_text(html[:match.start(1)] + payload + html[match.end(1):],
                    encoding="utf-8", newline="\n")

    csv_path = source / "Marts-and-Department-Stores.csv"
    with csv_path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        fields, rows = reader.fieldnames, list(reader)
    assert len(rows) == priced and "Price" in fields
    for row in rows:
        row["Price"] = str(prices[item_token(row["Item sprite"])])
    with csv_path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    for original, preview in (
        (page, source / "Heartfelt-Gold-v23-Guide-Preview.html"),
        (csv_path, source / "Marts-and-Department-Stores-v23-Preview.csv"),
    ):
        if preview.exists():
            preview.write_bytes(original.read_bytes())
    print(f"Added build-source prices to {priced} shop rows across {len(data['shops'])} counters")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    update(parser.parse_args().source)
