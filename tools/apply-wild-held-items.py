"""Apply only Species.c wild-held-item fields to an already built HG ROM.

Requires ndspy and gcc. The output differs from the base ROM only at the two
held-item fields in each affected personal-data record.
"""

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

import ndspy.rom


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def records(path):
    source = path.read_text(encoding="utf-8")
    starts = list(re.finditer(r"(?m)^\s*\[SPECIES_([A-Z0-9_]+)\]\s*=\s*\{", source))
    result = {}
    for index, match in enumerate(starts):
        block = source[match.end():starts[index + 1].start() if index + 1 < len(starts) else len(source)]
        held = re.search(
            r"\.wildHeldItems\s*=\s*\{\s*\.common\s*=\s*(ITEM_[A-Z0-9_]+)\s*,"
            r"\s*\.rare\s*=\s*(ITEM_[A-Z0-9_]+)", block
        )
        if not held:
            raise ValueError(f"Missing held items for {match.group(1)} in {path}")
        result[match.group(1)] = held.groups()
    if len(result) != len(starts):
        raise ValueError(f"Duplicate species records in {path}")
    return result


def values(engine, names):
    names = sorted(names)
    source = ("\n".join(names) + "\n").encode()
    output = subprocess.check_output(
        ["gcc", "-E", "-P", "-x", "c", "-include", "include/constants/species.h",
         "-include", "include/constants/item.h", "-"],
        input=source, cwd=engine,
    ).decode().splitlines()
    expanded = output[-len(names):]
    result = {}
    for name, expression in zip(names, expanded):
        if not re.fullmatch(r"[\d\s()+*/-]+", expression):
            raise ValueError(f"Unresolved constant {name}: {expression}")
        result[name] = int(eval(expression, {"__builtins__": {}}, {}))
    return result


def personal_archive(blob):
    rom = ndspy.rom.NintendoDSRom(bytes(blob))
    file_id = rom.filenames.idOf("a/0/0/2")
    fat_offset = int.from_bytes(blob[0x48:0x4C], "little") + file_id * 8
    start = int.from_bytes(blob[fat_offset:fat_offset + 4], "little")
    end = int.from_bytes(blob[fat_offset + 4:fat_offset + 8], "little")
    assert blob[start:start + 4] == b"NARC"
    assert int.from_bytes(blob[start + 8:start + 12], "little") == end - start
    btaf = start + 16
    assert blob[btaf:btaf + 4] == b"BTAF"
    count = int.from_bytes(blob[btaf + 8:btaf + 10], "little")
    btnf = btaf + int.from_bytes(blob[btaf + 4:btaf + 8], "little")
    assert blob[btnf:btnf + 4] == b"BTNF"
    gmif = btnf + int.from_bytes(blob[btnf + 4:btnf + 8], "little")
    assert blob[gmif:gmif + 4] == b"GMIF"
    data_start = gmif + 8
    return start, end, btaf + 12, data_start, count


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--old-engine", type=Path, required=True)
    parser.add_argument("--new-engine", type=Path, required=True)
    parser.add_argument("--new-constants-engine", type=Path,
                        help="Engine containing item/species headers when the new data is a source snapshot")
    parser.add_argument("--input-rom", type=Path, required=True)
    parser.add_argument("--base-rom", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)

    old_file = args.old_engine / "data/Species.c"
    new_file = args.new_engine / "data/Species.c"
    old = records(old_file)
    new = records(new_file)
    if old.keys() != new.keys():
        raise ValueError("Species sets differ")
    changed = {species: (old[species], new[species]) for species in old if old[species] != new[species]}
    if not changed:
        raise ValueError("No held-item changes found")
    names = {f"SPECIES_{species}" for species in old}
    names.update(item for pair in old.values() for item in pair)
    names.update(item for pair in new.values() for item in pair)
    old_values = values(args.old_engine, names)
    new_values = values(args.new_constants_engine or args.new_engine, names)
    if old_values != new_values:
        differing = [name for name in names if old_values[name] != new_values[name]]
        raise ValueError(f"Species or item IDs changed: {differing[:10]}")

    blob = bytearray(args.base_rom.read_bytes())
    base_sha = hashlib.sha256(blob).hexdigest()
    start, end, table, data_start, count = personal_archive(blob)
    if count != len(old):
        raise ValueError(f"Personal record count {count} differs from Species.c count {len(old)}")
    input_blob = args.input_rom.read_bytes()
    input_start, input_end, _, _, input_count = personal_archive(input_blob)
    if input_count != count or input_blob[input_start:input_end] != blob[start:end]:
        raise ValueError("Input and base ROM personal archives differ")

    allowed_positions = set()
    changes = []
    for species, previous in old.items():
        species_id = old_values[f"SPECIES_{species}"]
        if not 0 <= species_id < count:
            raise ValueError(f"Invalid species ID: {species}")
        record = table + 8 * species_id
        offset = int.from_bytes(blob[record:record + 4], "little")
        stop = int.from_bytes(blob[record + 4:record + 8], "little")
        if stop - offset < 0x10:
            raise ValueError(f"Short personal record: {species}")
        for column, old_token, new_token in zip(("common", "rare"), previous, new[species]):
            field = data_start + offset + (0x0C if column == "common" else 0x0E)
            old_id = old_values[old_token]
            new_id = new_values[new_token]
            if int.from_bytes(blob[field:field + 2], "little") != old_id:
                raise ValueError(f"Base ROM held item does not match Species.c: {species} {column}")
            if old_token != new_token:
                if not 0 <= new_id <= 0xFFFF:
                    raise ValueError(f"Item ID out of range: {new_token}")
                blob[field:field + 2] = new_id.to_bytes(2, "little")
                allowed_positions.update((field, field + 1))
        if species in changed:
            changes.append({"species": species, "old": previous, "new": new[species]})

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(blob)
    output_sha = hashlib.sha256(blob).hexdigest()
    original = args.base_rom.read_bytes()
    differing = {i for i, (before, after) in enumerate(zip(original, blob)) if before != after}
    if not differing or not differing <= allowed_positions:
        args.output.unlink(missing_ok=True)
        raise ValueError("Unexpected ROM byte differences")
    assert len(original) == len(blob)
    report = {
        "inputRomSha256": digest(args.input_rom),
        "baseRomSha256": base_sha,
        "outputRomSha256": output_sha,
        "outputRomBytes": len(blob),
        "oldSpeciesSha256": digest(old_file),
        "newSpeciesSha256": digest(new_file),
        "changedSpecies": len(changes),
        "changedRomBytes": len(differing),
        "scope": "Only wild held item fields in the personal archive changed",
        "changes": changes,
    }
    args.output.with_suffix(".held-items.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"PASS: changed {len(changes)} species, {len(differing)} ROM bytes; SHA-256 {output_sha}")


if __name__ == "__main__":
    main()
