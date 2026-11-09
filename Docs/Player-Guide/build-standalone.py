"""Bundle the reviewed player guide export into portable HTML and a small ZIP.

Usage:
    python Docs/Player-Guide/build-standalone.py --source "C:\\ROM-Hack\\Heartfelt-Gold\\Docs"

The source directory is the reviewed guide export. This script does not modify it.
"""

import argparse
import base64
import csv
import hashlib
import json
import re
import shutil
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SITE = HERE / "site"
APP_SCRIPT = HERE / "Guide-App.js"
RELEASE = HERE / "release.json"
PAGES = (
    ("Heartfelt-Gold-Walkthrough.html", "index.html"),
    ("Rematch-Trainer-Guide.html", "Rematch-Trainer-Guide.html"),
)
ZIP_NAME = "Heartfelt-Gold-Player-Guide-Offline.zip"


def sprite_paths(value):
    if isinstance(value, str):
        if value.startswith("Sprites/"):
            yield value
    elif isinstance(value, dict):
        for nested in value.values():
            yield from sprite_paths(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from sprite_paths(nested)


def check_gym_order(source, data):
    if data["mode"] != "main":
        return
    with (source / "Trainers-Story-Order.csv").open(encoding="utf-8-sig", newline="") as stream:
        csv_rows = list(csv.DictReader(stream))
    gym_groups = [group["id"] for group in data["trainerGroups"] if group["id"].startswith("gym-")]
    if len(gym_groups) != 16:
        raise ValueError("Expected 16 Gym chapters")
    for group in gym_groups:
        members = [t for t in data["trainers"] if t["group"] == group]
        ranks = [2 if t["bonus"] else 1 if t["major"] else 0 for t in members]
        if ranks != sorted(ranks) or ranks.count(1) != 1 or ranks.count(2) != 1:
            raise ValueError(f"Gym order needs normalization: {group}; run order-gym-trainers.py")
        ids = [t["id"] for t in members]
        csv_ids = list(dict.fromkeys(int(row["Trainer ID"]) for row in csv_rows
                                     if int(row["Trainer ID"]) in ids))
        if csv_ids != ids:
            raise ValueError(f"Trainer CSV Gym order differs from HTML: {group}")


def bundled_script(source):
    script = APP_SCRIPT.read_text(encoding="utf-8")
    if (source / "Guide-App.js").read_text(encoding="utf-8") != script:
        raise ValueError("Guide-App.js in the reviewed export differs from the versioned app script")
    changes = (
        (
            '  const REMATCH = DATA.mode === "rematch";',
            '  const REMATCH = DATA.mode === "rematch";\n'
            '  const spriteUrl = path => window.GUIDE_SPRITES[path] || path;',
        ),
        (
            'esc(src.startsWith("Sprites/Items/") ? src + "?v=2" : src)',
            'esc(spriteUrl(src))',
        ),
        ("esc(obj.front)", "esc(spriteUrl(obj.front))"),
        ("esc(t.portrait)", "esc(spriteUrl(t.portrait))"),
    )
    for old, new in changes:
        if script.count(old) != 1:
            raise ValueError(f"Guide-App.js changed: expected one {old!r}")
        script = script.replace(old, new)
    if "</script" in script.lower():
        raise ValueError("App script contains an HTML script terminator")
    return script


def build_page(source, input_name, output_name, script, css, version):
    html = (source / input_name).read_text(encoding="utf-8")
    match = re.search(r"window\.GUIDE_DATA=(\{.*?\});</script>", html)
    if not match:
        raise ValueError(f"No guide data in {input_name}")
    data = json.loads(match.group(1))
    check_gym_order(source, data)
    paths = sorted(set(sprite_paths(data)))
    sprites = {}
    for relative in paths:
        image = source / relative
        if not image.is_file():
            raise FileNotFoundError(image)
        sprites[relative] = "data:image/png;base64," + base64.b64encode(image.read_bytes()).decode("ascii")
    old_css = '<link rel="stylesheet" href="Guide-Style.css">'
    old_js = '<script src="Guide-App.js" defer></script>'
    if html.count(old_css) != 1 or html.count(old_js) != 1:
        raise ValueError(f"Unexpected CSS or JS link in {input_name}")
    html = html.replace(old_css, "<style>" + css + "</style>")
    html = html.replace(old_js, "")
    eyebrow = "POKÉMON HEARTFELT GOLD · PLAYER GUIDE"
    if html.count(eyebrow) != 1:
        raise ValueError(f"Unexpected guide heading in {input_name}")
    html = html.replace(eyebrow, f"{eyebrow} · {version}")
    if output_name == "Rematch-Trainer-Guide.html":
        html = html.replace('href="Heartfelt-Gold-Walkthrough.html"', 'href="index.html"')
    payload = json.dumps(sprites, separators=(",", ":"))
    html = html.replace(
        "</body></html>",
        "<script>window.GUIDE_SPRITES=" + payload + ";</script>"
        + "<script>" + script + "</script></body></html>",
    )
    if "Guide-App.js" in html or "Guide-Style.css" in html:
        raise ValueError(f"External app asset reference remains in {output_name}")
    output = SITE / output_name
    output.write_text(html, encoding="utf-8", newline="\n")
    print(f"{output_name}: {len(paths)} embedded sprites, {output.stat().st_size:,} bytes")


def build(source):
    SITE.mkdir(parents=True, exist_ok=True)
    release = json.loads(RELEASE.read_text(encoding="utf-8"))
    version = release["version"]
    patch = HERE.parent.parent / release["patch"]
    with patch.open("rb") as stream:
        patch_hash = hashlib.file_digest(stream, "sha256").hexdigest()
    if patch_hash != release["patchSha256"]:
        raise ValueError(f"Patch SHA-256 differs from release.json: {patch}")
    css = (source / "Guide-Style.css").read_text(encoding="utf-8")
    if "</style" in css.lower():
        raise ValueError("CSS contains an HTML style terminator")
    script = bundled_script(source)
    for input_name, output_name in PAGES:
        build_page(source, input_name, output_name, script, css, version)
    (SITE / RELEASE.name).write_bytes(RELEASE.read_bytes().replace(b"\r\n", b"\n"))
    for path in source.iterdir():
        if (path.is_file() and path.suffix.lower() in {".csv", ".md"}
                and path.name != "README-CSV-Review.md" and not path.stem.endswith("-v23-Preview")):
            (SITE / path.name).write_bytes(path.read_bytes().replace(b"\r\n", b"\n"))
    (SITE / "START-HERE.txt").write_text(
        f"Heartfelt Gold player guide — {version}\n\n"
        "1. Open index.html in a modern browser.\n"
        "2. Use the sidebar to browse the story, trainers, wild Pokémon, shops, items, and evolutions.\n"
        "3. Use Open rematch trainers for the separate rematch page.\n"
        "4. Search a section, choose Larger text, or print the current section as needed.\n\n"
        "The HTML pages include their sprites, styles, and code. Keep both HTML files in this folder "
        "for the rematch link to work. No internet connection is needed.\n"
        "See README-CSV-Review.md for data sources and limitations.\n",
        encoding="utf-8", newline="\n",
    )
    (SITE / "README-CSV-Review.md").write_text(
        f"# Heartfelt Gold player guide notes — {version}\n\n"
        "Open `index.html` locally, or use the published guide at "
        "https://trinsic64.github.io/Heartfelt-Gold/. The two HTML pages include their sprites, "
        "styles, and code. Rematches have a separate page; bonus battles stay with story trainers. "
        "The first Elite Four and Champion run follows eight badges, while the second run and its "
        "bonus battles follow Gym #16 Blue.\n\n"
        f"This guide is bundled with the {version} patch named in `release.json`. The patch was decoded "
        "against the documented clean USA ROM and matched the recorded hg-engine build hash.\n\n"
        "The trainer, wild encounter, shop, and evolution tables reflect the source data "
        "used for the v23 hg-engine build. Twenty-one player-facing trainer parties changed "
        "since v1.0.11; internal dummy Trainer 0 is omitted. Cherrygrove Mart now stocks Cherish "
        "Ball, and both Frillish forms evolve at level 40. Wild held items match the updated "
        "`HG-Engine/data/Species.c` snapshot, including form-specific rows. Ground pickups come from the named Release-v2 "
        "event extraction and hidden "
        "item parameter table. Two visible pickup objects have unresolved item identities. "
        "The 89 static encounter rows use v22 Test levels and follow the reviewed Markdown guide; "
        "the unbound Union Cave Victini command is excluded. Parent areas are traced through inbound "
        "warps or bound same-map event objects; script and placement "
        "data do not by themselves establish reachability or unlock conditions. Individual guide rows "
        "have not all been independently checked against gameplay.\n\n"
        "Trainer cards show the in-battle Mega sprite, ability, and typing where the build's Mega "
        "Stone/form tables resolve a Mega species; the trainer CSV keeps the base party species "
        "stored in the ROM. Four Tatsugiri with Tatsugirinite and Blue's Floette with Floettite "
        "retain their base display because the configured target forms do not resolve to Mega "
        "species in this build. Wild encounter display is unchanged.\n\n"
        "See `Release-v22-Item-Audit.md` for the item audit. "
        "`Item-Locations.csv` is the older Retiled Expansion item list and remains historical. "
        "Form-specific encounter rows and evolution icons were resolved against engine species IDs. "
        "The v23 input fixed Diglett's Cave map matrix 2 by adding map member 976; those map archives "
        "were preserved byte for byte in the built ROM.\n",
        encoding="utf-8", newline="\n",
    )
    (SITE / ".nojekyll").write_text("", encoding="utf-8")
    archive = SITE / ZIP_NAME
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for path in sorted(SITE.iterdir()):
            if path.is_file() and path != archive:
                info = zipfile.ZipInfo(path.name, date_time=(1980, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o644 << 16
                z.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    with zipfile.ZipFile(archive) as z:
        if z.testzip() is not None:
            raise ValueError("ZIP integrity check failed")
        if z.read("index.html") != (SITE / "index.html").read_bytes():
            raise ValueError("ZIP guide does not match the site")
    print(f"{archive.name}: {archive.stat().st_size:,} bytes")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True, help="Reviewed guide export directory")
    build(parser.parse_args().source)
