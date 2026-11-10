"""Audit field battle scripts against the release ROM and update the guide export."""

import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import re
import runpy
import struct


HERE = Path(__file__).resolve().parent
RELEASE = json.loads((HERE / "release.json").read_text(encoding="utf-8"))
HQ = [223, 224, 216, 470, 218, 219, 220, 468, 469, 222, 404, 488, 479, 499, 675]
KIMONO = [162, 160, 164, 161, 163]
RAID = [185, 186, 187, 188, 198, 189, 190, 191, 471, 192, 200, 472, 487,
        271, 288, 289, 14, 193, 195, 199, 228, 283, 196, 197, 227, 706, 478, 485]
DEN = [733, 734, 735, 736, 737]
SILVER = [489, 490, 491]
PARTNERS = {675, 735, 736, 737}
DOJO = "Saffron City › Fighting Dojo"
THEATER_STAGE = "29 Ecruteak Dance Theater / To the Pokémon League"
ARCHIVES = {"scripts": "a/0/1/2", "eventFiles": "a/0/3/2", "dynamicHeaders": "a/0/5/0"}
SECTION = re.compile(r"(?m)^(Script|Function|Action) (\d+):[ \t]*$")
BATTLE = re.compile(r"(?m)^[ \t]*(TrainerBattle|Battle2vs2)[ \t]+([^\r\n]+)")


def unpacked_members(project, name):
    return [path.read_bytes() for path in sorted((project / "unpacked" / name).iterdir())
            if path.name.isdigit()]


def trainer_id(token):
    if token == "TRAINER_NONE":
        return 0
    if token.startswith("TRAINER_"):
        return int(token.rsplit("_", 1)[1])
    return int(token, 0)


def collect_audit(rom_path, project, disassembly):
    import ndspy.narc
    import ndspy.rom

    raw = rom_path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest not in {patch["decodedRomSha256"] for patch in RELEASE["patches"].values()}:
        raise ValueError("Audit ROM does not match the release manifest")
    rom = ndspy.rom.NintendoDSRom(raw)
    archives = {}
    for name, path in ARCHIVES.items():
        members = ndspy.narc.NARC(rom.getFileByName(path)).files
        if members != unpacked_members(project, name) or members != unpacked_members(disassembly, name):
            raise ValueError(f"{name} differs between the ROM and DSPRE exports. Refresh the disassembly.")
        archives[name] = members

    messages = json.loads((project / "expanded/textArchives/0279.json").read_text(encoding="utf-8-sig"))["messages"]
    map_names = rom.getFileByName("fielddata/maptable/mapname.bin")
    headers = defaultdict(list)
    for index, header in enumerate(archives["dynamicHeaders"]):
        script = struct.unpack_from("<H", header, 6)[0]
        internal = map_names[index * 16:(index + 1) * 16].split(b"\0", 1)[0].decode("ascii")
        headers[script].append((index, messages[header[18]]["en_US"], internal))

    banks = {}
    for bank, binary in enumerate(archives["scripts"]):
        path = disassembly / f"expanded/scripts/{bank:04}.script"
        text = path.read_text(encoding="utf-8-sig")
        sections = list(SECTION.finditer(text))
        commands = set()
        calls = []
        for index, section in enumerate(sections):
            end = sections[index + 1].start() if index + 1 < len(sections) else len(text)
            for command in BATTLE.finditer(text, section.end(), end):
                name, args = command[1], command[2].split()
                if name == "TrainerBattle":
                    first, second, result, mode = map(trainer_id, args)
                    encoded = struct.pack("<HHHBB", 0xD5, first, second, result, mode)
                    opponents, partner = [first, second], 0
                else:
                    partner, first, second, mode = map(trainer_id, args)
                    encoded = struct.pack("<HHHHB", 0x232, partner, first, second, mode)
                    opponents = [first, second]
                commands.add(encoded)
                calls.append((f"{section[1]} {section[2]}", [tid for tid in opponents if tid], partner))
        if calls:
            if any(command not in binary for command in commands):
                raise ValueError(f"Battle commands do not match the ROM in script bank {bank:04}")
            banks[bank] = calls

    for bank, expected in {89: {223, 224}, 90: {479, 499}, 91: {488}, 928: {601, *KIMONO},
                           111: {733, 734}, 819: set(SILVER), 832: set(range(712, 728))}.items():
        assert {tid for _, opponents, _ in banks[bank] for tid in opponents} == expected, bank
    theater_order = list(dict.fromkeys(tid for _, opponents, _ in banks[928] for tid in opponents))
    assert theater_order == [601, *KIMONO]

    # Decode the normal trainer object scripts on each HQ floor, in addition to battle commands.
    for header_id, expected in {247: {216, 470}, 248: {218, 219, 220}, 249: {222, 404, 468, 469}}.items():
        header = archives["dynamicHeaders"][header_id]
        event_id = struct.unpack_from("<H", header, 16)[0]
        event = archives["eventFiles"][event_id]
        start = 4 + 20 * struct.unpack_from("<I", event)[0]
        count = struct.unpack_from("<I", event, start)[0]
        objects = [struct.unpack_from("<6H", event, start + 4 + 32 * index) for index in range(count)]
        found = {script - 2999 for _, _, _, kind, _, script in objects if kind == 1 and 3000 <= script < 5000}
        assert found == expected, header_id

    return digest, headers, banks


def apply_placements(main, rematches):
    trainers = {trainer["id"]: trainer for trainer in main["trainers"]}
    groups = {group["id"]: group for group in main["trainerGroups"]}
    chapters = {chapter["number"]: chapter for chapter in main["chapters"]}
    chapters[29]["label"] = THEATER_STAGE
    for trainer in trainers.values():
        if trainer["stage"].startswith("29 "):
            trainer["stage"] = THEATER_STAGE

    def place(ids, group, label, chapter, group_order, first_order):
        groups[group] = {"id": group, "label": label, "order": group_order}
        for index, tid in enumerate(ids):
            trainers[tid].update(group=group, stage=chapters[chapter]["label"],
                                 order=round(first_order + index / 100, 2))

    groups["stage-13"]["label"] = "13 Goldenrod City"
    groups["stage-23"]["label"] = "23 Route 43 / Lake of Rage"
    place(HQ, "rocket-hq", "Team Rocket HQ - Mahogany Town", 23, 231, 43)
    place([601], "dance-first", "Ecruteak Dance Theater - First visit", 16, 160, 22)
    place(KIMONO, "dance-kimono", "Ecruteak Dance Theater - Kimono Girls (after 8 badges)", 29, 289, 53.8)
    place(RAID, "stage-25", "25 Goldenrod Radio Tower takeover", 25, 250, 45)
    place(DEN, "dragon-den-tag", "Dragon’s Den tag battle (after Mt. Moon)", 41, 419.1, 92)
    place(SILVER, "silver-indigo", "Silver at Indigo Plateau (after Dragon’s Den)", 41, 419.2, 93)

    notes = {
        **{tid: "B1F security statues can trigger these two Grunt battles in sequence." for tid in (223, 224)},
        488: "B3F password-room battle. Follow the Murkrow back to the B2F generator door afterward.",
        479: "B2F generator door. Double battle with the Grunt, with Lance on your side.",
        499: "B2F generator door. Double battle with Ariana, with Lance on your side.",
        675: "Lance fights alongside you against Ariana and the Grunt at the B2F generator door.",
        601: "First Dance Theater visit in Ecruteak. Challenge the Grunt harassing the dancer.",
        **{tid: f"Battle {index} of 5 on the return visit after earning all eight Johto badges and completing the Dragon’s Den test."
           for index, tid in enumerate(KIMONO, 1)},
        **{tid: "Optional tag battle after facing Silver at Mt. Moon. Silver is your partner against Lance and Clair."
           for tid in DEN},
        **{tid: "Optional follow-up after the Dragon’s Den tag battle. Check the League entrance on Monday or Wednesday."
           for tid in SILVER},
        700: "Optional Celebi time-travel event. The script binds this team to the Tohjo Falls hidden room.",
    }
    for tid, note in notes.items():
        trainers[tid]["storyNote"] = note
    for tid in PARTNERS:
        trainers[tid]["partner"] = True

    for trainer in rematches["trainers"]:
        if 712 <= trainer["id"] <= 727:
            trainer["location"] = DOJO
            trainer["storyNote"] = "Arrange the rematch by phone, then meet the Gym Leader at the Fighting Dojo."

    in_use = {trainer["group"] for trainer in trainers.values()}
    main["trainerGroups"] = sorted((group for group in groups.values() if group["id"] in in_use),
                                   key=lambda group: group["order"])
    group_rank = {group["id"]: index for index, group in enumerate(main["trainerGroups"])}
    reordered = set(HQ + KIMONO + RAID + DEN + SILVER)
    main["trainers"].sort(key=lambda t: (group_rank[t["group"]], t["order"] if t["id"] in reordered else 0))


def write_report(path, digest, headers, banks, main, rematches):
    parties = {t["id"]: t for t in main["trainers"] + rematches["trainers"]}
    ids = {tid for calls in banks.values() for _, opponents, partner in calls for tid in [*opponents, partner]
           if 0 < tid < 0x4000}
    if not ids <= parties.keys():
        raise ValueError(f"Scripted parties missing from the guide: {sorted(ids - parties.keys())}")
    report = [f"# Scripted trainer audit for Heartfelt Gold {RELEASE['version']}", "",
              f"Reviewed the v24 release ROM (`{digest}`). All 1,139 script banks, 578 event members, "
              "and 627 map headers matched the reviewed DSPRE data. The v24 export supplied the disassembly "
              "except for Seafoam Islands bank 0015, which came from a later export whose bank matched the release byte for byte.", "",
              f"Found {sum(map(len, banks.values()))} battle references in the disassembly of {len(banks)} banks. "
              f"All {len(ids)} distinct literal party IDs are present in the story or rematch guide. "
              "Alternate cutscene paths and shared script offsets can repeat a party reference. Bank 0953 uses variables for ordinary "
              "overworld trainers. The Victoria call in common bank 0003 has no direct map header, so her regular "
              "Goldenrod Gym placement is used.", "",
              "## Progression checks", "",
              "- **Gym and League victories.** The v24 scripts update the level cap after Gym wins "
              "and at selected League victories. The walkthrough cards show those values. "
              "Several bonus-battle branches heal the party before the optional challenge.", "",
              "- **Team Rocket HQ.** Headers 247–249 bind B1F–B3F. The B1F alarm scripts call Grunts 223 and 224. "
              "Nine additional parties are bound to trainer objects across the three floors. Petrel is on B3F. "
              "The B2F generator-door battle calls Ariana and Grunt 499 with Lance 675 as the player’s partner. "
              "The group follows the route through the base. Optional trainer order can vary.",
              "- **Ecruteak Dance Theater.** Header 86 and bank 0928 bind both visits. Script 4 calls Grunt 601 "
              "on the first visit. The later branches all call Zuki → Naoko → Miki → Sayo → Kuni. "
              "The dialogue refers to completing the Dragon’s Den test and defeating Team Rocket in Goldenrod. "
              "The guide places the five battles after the eight Johto badges, before Routes 26–27.",
              "- **Goldenrod takeover.** The Radio Tower and Goldenrod Tunnel B2F/Warehouse trainers appear in the "
              "raid after Pryce. The scripted parties include Petrel, Silver’s three starter variants, and Archer.",
              "- **Silver follow-up.** Mt. Moon bank 0007 sets `0x40FC` to 1. The Dragon’s Den tag-battle trigger "
              "uses that state and its win sets it to 2. League entrance bank 0819 checks that progression and "
              "weekday values 1 or 3. These follow-up battles are grouped with the Mt. Moon stage, with the actual "
              "battle locations shown on the cards.",
              "- **Gym rematches.** Bank 0832 (header 398) calls all 16 Gym rematch teams at the Saffron Fighting "
              "Dojo. The rematch CSV and HTML show the Dojo and keep each team's original Gym stage for reference.", "",
              "The audit confirms the script operands and map associations. Conditional branches and optional events "
              "were read from source, and the audit did not play through every trigger.", "",
              "## Field script inventory", "",
              "| Bank | Map header and area | Opponent IDs | Partner IDs |", "| --- | --- | --- | --- |"]
    for bank, calls in banks.items():
        maps = "; ".join(f"{i} {name} ({internal})" for i, name, internal in headers[bank]) or "Common / no direct map header"
        opponents = sorted({tid for _, ids_in_call, _ in calls for tid in ids_in_call})
        partners = sorted({partner for _, _, partner in calls if partner})
        fmt = lambda values: ", ".join(str(v) if v < 0x4000 else f"variable `0x{v:04X}`" for v in values) or "—"
        report.append(f"| {bank:04} | {maps} | {fmt(opponents)} | {fmt(partners)} |")
    path.write_text("\n".join(report) + "\n", encoding="utf-8", newline="\n")


def update_export(source, digest, headers, banks):
    helpers = runpy.run_path(str(HERE / "fix-postgame-league.py"))
    main_path = source / "Heartfelt-Gold-Walkthrough.html"
    rematch_path = source / "Rematch-Trainer-Guide.html"
    html, match, main = helpers["read_page"](main_path)
    rematch_html, rematch_match, rematches = helpers["read_page"](rematch_path)
    apply_placements(main, rematches)
    write_report(source / "Scripted-Trainer-Audit.md", digest, headers, banks, main, rematches)
    for data, filename in ((main, "Trainers-Story-Order.csv"), (rematches, "Rematch-Trainers.csv")):
        path = source / filename
        fields, rows = helpers["read_csv"](path)
        trainers = {t["id"]: t for t in data["trainers"]}
        rank = {tid: index for index, tid in enumerate(trainers)}
        for row in rows:
            trainer = trainers[int(row["Trainer ID"])]
            row["Story stage (approx.)"] = trainer["stage"]
            row["Location"] = trainer["location"]
            if trainer.get("partner"):
                row["Battle kind"] = "Battle partner"
        if data is main:
            rows.sort(key=lambda row: rank[int(row["Trainer ID"])])
        helpers["write_csv"](path, fields, rows)
    helpers["save_page"](main_path, html, match, main)
    helpers["save_page"](rematch_path, rematch_html, rematch_match, rematches)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("rom", "project", "disassembly", "source"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    args = parser.parse_args()
    update_export(args.source, *collect_audit(args.rom, args.project, args.disassembly))
