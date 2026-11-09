"""Put each Gym's trainers before its Leader and the Leader's Bonus Battle.

Preserves the audited order of ordinary Gym Trainers and the party-slot order
inside each trainer. Run on the reviewed export before build-standalone.py.
"""

import argparse
import csv
import json
import re
from pathlib import Path


DATA_PATTERN = re.compile(r"window\.GUIDE_DATA=(\{.*?\});</script>")


def gym_rank(trainer):
    return 2 if trainer["bonus"] else 1 if trainer["major"] else 0


def fix(source):
    page = source / "Heartfelt-Gold-Walkthrough.html"
    html = page.read_text(encoding="utf-8")
    match = DATA_PATTERN.search(html)
    if not match:
        raise ValueError(f"Guide data not found: {page}")
    data = json.loads(match.group(1))
    trainers = data["trainers"]
    gym_groups = [group["id"] for group in data["trainerGroups"]
                  if group["id"].startswith("gym-")]
    assert len(gym_groups) == 16
    changed = 0
    ordered_ids = {}
    for group in gym_groups:
        positions = [i for i, trainer in enumerate(trainers) if trainer["group"] == group]
        before = [trainers[i] for i in positions]
        assert sum(t["major"] and not t["bonus"] for t in before) == 1, group
        assert sum(t["bonus"] for t in before) == 1, group
        after = sorted(before, key=gym_rank)
        changed += before != after
        for position, trainer in zip(positions, after):
            trainers[position] = trainer
        ordered_ids[group] = [trainer["id"] for trainer in after]

    if changed:
        payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
        page.write_text(html[:match.start(1)] + payload + html[match.end(1):],
                        encoding="utf-8", newline="\n")

    csv_path = source / "Trainers-Story-Order.csv"
    with csv_path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        fields, rows = reader.fieldnames, list(reader)
    csv_changed = 0
    for group, ids in ordered_ids.items():
        member_ids = set(ids)
        positions = [i for i, row in enumerate(rows) if int(row["Trainer ID"]) in member_ids]
        before = [rows[i] for i in positions]
        by_id = {trainer_id: [row for row in before if int(row["Trainer ID"]) == trainer_id]
                 for trainer_id in ids}
        after = [row for trainer_id in ids for row in by_id[trainer_id]]
        assert len(after) == len(before) and all(by_id.values()), group
        csv_changed += before != after
        for position, row in zip(positions, after):
            rows[position] = row
    if csv_changed:
        with csv_path.open("w", encoding="utf-8-sig", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)

    for original, preview in (
        (page, source / "Heartfelt-Gold-v23-Guide-Preview.html"),
        (csv_path, source / "Trainers-Story-Order-v23-Preview.csv"),
    ):
        if preview.exists():
            preview.write_bytes(original.read_bytes())
    print(f"Gym order normalized: {changed} HTML groups, {csv_changed} CSV groups")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    fix(parser.parse_args().source)
