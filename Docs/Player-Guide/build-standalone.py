"""Bundle the reviewed player guide export into portable HTML and a small ZIP.

Usage:
    python Docs/Player-Guide/build-standalone.py --source "C:\\ROM-Hack\\Heartfelt-Gold\\Docs"

The source directory is the reviewed guide export. This script does not modify it.
"""

import argparse
import base64
import json
import re
import shutil
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SITE = HERE / "site"
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


def bundled_script(source):
    script = (source / "Guide-App.js").read_text(encoding="utf-8")
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


def build_page(source, input_name, output_name, script, css):
    html = (source / input_name).read_text(encoding="utf-8")
    match = re.search(r"window\.GUIDE_DATA=(\{.*?\});</script>", html)
    if not match:
        raise ValueError(f"No guide data in {input_name}")
    data = json.loads(match.group(1))
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
    output.write_text(html, encoding="utf-8")
    print(f"{output_name}: {len(paths)} embedded sprites, {output.stat().st_size:,} bytes")


def build(source):
    SITE.mkdir(parents=True, exist_ok=True)
    css = (source / "Guide-Style.css").read_text(encoding="utf-8")
    if "</style" in css.lower():
        raise ValueError("CSS contains an HTML style terminator")
    script = bundled_script(source)
    for input_name, output_name in PAGES:
        build_page(source, input_name, output_name, script, css)
    for path in source.iterdir():
        if path.is_file() and path.suffix.lower() in {".csv", ".md"} and path.name != "README-CSV-Review.md":
            shutil.copy2(path, SITE / path.name)
    (SITE / "START-HERE.txt").write_text(
        "Heartfelt Gold player guide\n\n"
        "1. Open index.html in a modern browser.\n"
        "2. Use the sidebar to browse the story, trainers, wild Pokémon, shops, items, and evolutions.\n"
        "3. Use Open rematch trainers for the separate rematch page.\n"
        "4. Search a section, choose Larger text, or print the current section as needed.\n\n"
        "The HTML pages include their sprites, styles, and code. Keep both HTML files in this folder "
        "for the rematch link to work. No internet connection is needed.\n"
        "See README-CSV-Review.md for data sources and limitations.\n",
        encoding="utf-8",
    )
    (SITE / "README-CSV-Review.md").write_text(
        "# Heartfelt Gold player guide notes\n\n"
        "Open `index.html` locally, or use the published guide at "
        "https://trinsic64.github.io/Heartfelt-Gold/. The two HTML pages include their sprites, "
        "styles, and code. Rematches have a separate page; bonus battles stay with story trainers.\n\n"
        "The trainer, wild encounter, shop, and evolution tables reflect the current authoring data "
        "used for this guide. Ground pickups come from the named Release-v2 event extraction and hidden "
        "item parameter table. Two visible pickup objects have unresolved item identities. "
        "Static encounter parent areas are traced through direct inbound warps; script and placement "
        "data do not by themselves establish reachability or unlock conditions. The currently released "
        "patch has not been independently checked against every table.\n\n"
        "See `Release-v22-Item-Audit.md` for the item audit. "
        "`Item-Locations.csv` is the older Retiled Expansion item list and remains historical. "
        "Form-specific encounter rows and evolution icons were resolved against engine species IDs.\n",
        encoding="utf-8",
    )
    (SITE / ".nojekyll").write_text("", encoding="utf-8")
    archive = SITE / ZIP_NAME
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for path in sorted(SITE.iterdir()):
            if path.is_file() and path != archive:
                z.write(path, path.name)
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
