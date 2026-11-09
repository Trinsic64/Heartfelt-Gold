# Pokémon Heartfelt Gold v1.0.11

This update gives wild Pokémon the revised common and rare held items from the newer `Species.c` data. It uses the same v22 Test game input and hg-engine build as v1.0.10, with only the personal-data held item fields changed. The online and offline guides now show those items and the reviewed v22 Test static encounter levels.

## Downloads and guide

- [Download the v1.0.11 xDelta patch](https://github.com/Trinsic64/Heartfelt-Gold/releases/download/heartfelt-v1.0.11/Heartfelt-Gold-v1.0.11-Patch.xdelta).
- [Open the v1.0.11 guide online](https://trinsic64.github.io/Heartfelt-Gold/).
- [Download the offline guide ZIP](https://github.com/Trinsic64/Heartfelt-Gold/releases/download/heartfelt-v1.0.11/Heartfelt-Gold-Player-Guide-Offline.zip), extract it, then double-click `index.html`. Keep the extracted files together so the Rematch Trainers link works.
- [Download checksums for both files](https://github.com/Trinsic64/Heartfelt-Gold/releases/download/heartfelt-v1.0.11/RELEASE-CHECKSUMS-HEARTFELT-v1.0.11.sha256).

The wild atlas lists the updated held items for all 3,178 encounter rows, with form-specific item icons where available. The static atlas now follows the 89 entries in the reviewed v22 Test Markdown guide. It includes Spectrier, Glastrier and Phione, and omits an unbound Union Cave Victini script command. The bound Liberty Garden Victini entry remains.

## Apply the patch

Use a legally obtained, clean **Pokémon HeartGold (USA)** ROM with SHA-256 `65f02a56842b75aa92d775d56d657a56fe3fa993550b04dc20704ab82d760105`. Apply `Heartfelt-Gold-v1.0.11-Patch.xdelta` directly to that clean ROM using an xDelta patcher. Do not apply it over v1.0.10 or any other patched ROM.

Back up your in-game save before switching versions. A copied save loaded and reached gameplay in a headless v1.0.11 emulator check. A new save/reload test and full playthrough were not performed. Use the in-game save rather than an emulator save state from an older ROM.

## Build and verification

| Artifact | Size | SHA-256 |
| --- | ---: | --- |
| v1.0.11 xDelta patch | 34,200,440 bytes | `33a031ff79159a74ffaba3f5a4a2c0c13db1f316c55632bef553b7931d221e5f` |
| Offline guide ZIP | 3,721,189 bytes | `12e282dda569e95d22188a03e02298c4056e5a9404205e1b3218aa85bcc2ed39` |
| Decoded ROM (verification only; not distributed) | 207,711,200 bytes | `98342f8cb080f50a33b71a9f807571e9024471449ca9ad261de856d55cc1f5aa` |

The patch decoded against the documented clean USA source and matched the tested ROM byte for byte. Compared with the v1.0.10 ROM, exactly 1,949 bytes changed, all inside the two wild held item fields of 628 species records. The [committed Species.c snapshot](HG-Engine/data/Species.c) matches the held item source used for this build (SHA-256 `2cf1bc97ee2899803ffaa5441fd8479be9aa7a1f12df049d48158d7dc1da2f5c`). The base engine source commit remains `23c4f1ab256ace92bcba4585df3c0b2959741676`.

The v22 Test static levels were verified from the script export by the project author. Listing a script and its parent area does not prove that an encounter is reachable or unlocked. Two visible ground pickup objects remain unresolved in the item audit. See the [guide review notes](Docs/Player-Guide/site/README-CSV-Review.md).

Only the patch and guide are distributed. No ROM or save is included.
