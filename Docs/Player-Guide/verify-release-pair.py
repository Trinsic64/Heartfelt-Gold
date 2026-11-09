"""Check that the published guide, offline ZIP, and patch name the same release."""

import hashlib
import json
import zipfile
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
print(f"PASS: {version} patch, site, offline ZIP, checksums, and release notes agree")
