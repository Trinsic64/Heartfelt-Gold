"""Place the second Pokémon League run after Blue in the reviewed guide export.

Run before build-standalone.py when updating the v1.0.12 guide source directory.
The five second-run parties (701–705) belong beside their bonus battles
(759–763), not in the generic rematch guide or first League chapters.
"""

import argparse
import csv
import json
import re
from pathlib import Path


FIRST = {"Will": (245, 746), "Koga": (247, 747), "Bruno": (418, 748),
         "Karen": (246, 749), "Lance": (244, 750)}
SECOND = {"Will": (702, 759), "Koga": (703, 760), "Bruno": (704, 761),
          "Karen": (705, 762), "Lance": (701, 763)}
NAMES = list(SECOND)
SECOND_MAIN = {pair[0] for pair in SECOND.values()}
SECOND_BONUS = {pair[1] for pair in SECOND.values()}
STAGE = "43 Elite Four and Champion Post Game (after 16 badges)"
DATA_PATTERN = re.compile(r"window\.GUIDE_DATA=(\{.*?\});</script>")


def read_page(path):
    html = path.read_text(encoding="utf-8")
    match = DATA_PATTERN.search(html)
    if not match:
        raise ValueError(f"Guide data not found: {path}")
    return html, match, json.loads(match.group(1))


def save_page(path, html, match, data):
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    path.write_text(html[:match.start(1)] + payload + html[match.end(1):],
                    encoding="utf-8", newline="\n")


def shift_stage(stage):
    match = re.match(r"^(43|44) (.*)$", stage)
    return f"{int(match.group(1)) + 1:02} {match.group(2)}" if match else stage


def shift_chapters(data):
    for chapter in data["chapters"]:
        if chapter["number"] in (43, 44):
            chapter["number"] += 1
            chapter["label"] = shift_stage(chapter["label"])
    data["chapters"].insert(next(i for i, c in enumerate(data["chapters"])
                                 if c["number"] == 44),
                            {"number": 43, "label": STAGE})
    for trainer in data["trainers"]:
        trainer["stage"] = shift_stage(trainer["stage"])
    for key in ("wild", "shops", "items", "statics"):
        for entry in data.get(key, []):
            if entry.get("chapter") in (43, 44):
                entry["chapter"] += 1


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        return reader.fieldnames, list(reader)


def write_csv(path, fields, rows):
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def fix(source):
    main_path = source / "Heartfelt-Gold-Walkthrough.html"
    rematch_path = source / "Rematch-Trainer-Guide.html"
    main_html, main_match, main = read_page(main_path)
    rematch_html, rematch_match, rematch = read_page(rematch_path)
    main_ids = {t["id"] for t in main["trainers"]}
    rematch_ids = {t["id"] for t in rematch["trainers"]}
    if SECOND_MAIN <= main_ids and not SECOND_MAIN & rematch_ids:
        assert all(next(t for t in main["trainers"] if t["id"] == mid)["stage"] == STAGE
                   for mid in SECOND_MAIN)
        if main["counts"]["rematches"] != len(rematch["trainers"]):
            main["counts"]["rematches"] = len(rematch["trainers"])
            save_page(main_path, main_html, main_match, main)
            preview = source / "Heartfelt-Gold-v23-Guide-Preview.html"
            if preview.exists():
                preview.write_bytes(main_path.read_bytes())
        print("Postgame League chapters already fixed")
        return
    assert SECOND_MAIN <= rematch_ids and SECOND_BONUS <= main_ids
    assert not SECOND_MAIN & main_ids
    assert all(next(t for t in main["trainers"] if t["id"] == mid)["group"] == f"league-{name.lower()}"
               for name, (mid, _) in FIRST.items())

    shift_chapters(main)
    shift_chapters(rematch)
    main["chapters"][next(i for i, c in enumerate(main["chapters"]) if c["number"] == 31)]["label"] = \
        "31 Elite Four and Champion (after 8 badges)"
    rematch["chapters"][next(i for i, c in enumerate(rematch["chapters"]) if c["number"] == 31)]["label"] = \
        "31 Elite Four and Champion (after 8 badges)"

    for group in main["trainerGroups"]:
        if group["id"].startswith("league-"):
            group["label"] += " (after 8 badges)"
        elif group["id"] in ("stage-43", "stage-44"):
            group["id"] = f"stage-{int(group['id'][-2:]) + 1}"
            group["label"] = shift_stage(group["label"])
            group["order"] += 10
    insertion = next(i for i, group in enumerate(main["trainerGroups"])
                     if group["id"] == "stage-44")
    main["trainerGroups"][insertion:insertion] = [
        {"id": f"postleague-{name.lower()}",
         "label": (f"Elite Four #{index} {name}" if index < 5 else "Champion Lance")
                  + " - Post Game (after 16 badges)",
         "order": 430 + index}
        for index, name in enumerate(NAMES, 1)
    ]
    for trainer in main["trainers"]:
        if trainer["id"] in SECOND_BONUS:
            trainer["stage"] = STAGE
            trainer["group"] = f"postleague-{trainer['name'].lower()}"
        elif trainer["group"] in ("stage-43", "stage-44"):
            trainer["group"] = f"stage-{int(trainer['group'][-2:]) + 1}"

    second_main = {t["id"]: t for t in rematch["trainers"] if t["id"] in SECOND_MAIN}
    rematch["trainers"] = [t for t in rematch["trainers"] if t["id"] not in SECOND_MAIN]
    for index, name in enumerate(NAMES, 1):
        mid, bid = SECOND[name]
        trainer = second_main[mid]
        assert trainer["name"] == name and trainer["rematchInfo"]["variant"] == "Second run"
        trainer.pop("rematchInfo")
        trainer["rematch"] = False
        trainer["stage"] = STAGE
        trainer["group"] = f"postleague-{name.lower()}"
        trainer["order"] = next(t for t in main["trainers"] if t["id"] == bid)["order"]
        main["trainers"].append(trainer)
    main["trainers"].sort(key=lambda t: (t["order"], t["id"]))
    main["counts"]["trainers"] = len(main["trainers"])
    main["counts"]["rematches"] = len(rematch["trainers"])
    rematch["counts"]["rematches"] = len(rematch["trainers"])

    story_path = source / "Trainers-Story-Order.csv"
    rematch_csv_path = source / "Rematch-Trainers.csv"
    story_fields, story_rows = read_csv(story_path)
    rematch_fields, rematch_rows = read_csv(rematch_csv_path)
    assert {int(r["Trainer ID"]) for r in rematch_rows if int(r["Trainer ID"]) in SECOND_MAIN} == SECOND_MAIN
    for row in story_rows + rematch_rows:
        row["Story stage (approx.)"] = shift_stage(row["Story stage (approx.)"])
    bonus_rows = {bid: [r for r in story_rows if int(r["Trainer ID"]) == bid]
                  for _, bid in SECOND.values()}
    second_rows = {mid: [r for r in rematch_rows if int(r["Trainer ID"]) == mid]
                   for mid, _ in SECOND.values()}
    assert all(len(rows) == 6 for rows in list(bonus_rows.values()) + list(second_rows.values()))
    story_rows = [r for r in story_rows if int(r["Trainer ID"]) not in SECOND_BONUS]
    rematch_rows = [r for r in rematch_rows if int(r["Trainer ID"]) not in SECOND_MAIN]
    insert_at = next(i for i, row in enumerate(story_rows) if row["Trainer ID"] == "260")
    postgame_rows = []
    for name in NAMES:
        mid, bid = SECOND[name]
        for row in second_rows[mid]:
            converted = {field: row[field] for field in story_fields}
            converted["Story stage (approx.)"] = STAGE
            converted["Battle kind"] = "Main / special battle"
            postgame_rows.append(converted)
        for row in bonus_rows[bid]:
            row["Story stage (approx.)"] = STAGE
            postgame_rows.append(row)
    story_rows[insert_at:insert_at] = postgame_rows
    assert len(postgame_rows) == 60
    write_csv(story_path, story_fields, story_rows)
    write_csv(rematch_csv_path, rematch_fields, rematch_rows)
    save_page(main_path, main_html, main_match, main)
    save_page(rematch_path, rematch_html, rematch_match, rematch)
    for original, preview in (
        (main_path, source / "Heartfelt-Gold-v23-Guide-Preview.html"),
        (story_path, source / "Trainers-Story-Order-v23-Preview.csv"),
    ):
        if preview.exists():
            preview.write_bytes(original.read_bytes())
    print("Moved second-run League parties and bonuses after Gym #16 Blue")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    fix(parser.parse_args().source)
