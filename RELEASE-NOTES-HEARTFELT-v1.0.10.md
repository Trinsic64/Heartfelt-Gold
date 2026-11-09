# Pokémon Heartfelt Gold v1.0.10

This release rebuilds the supplied v22 test game content with the current hg-engine port. The player guide and offline guide ZIP are published with the same version as the patch.

## Downloads and guide

- [Download the v1.0.10 xDelta patch](https://github.com/Trinsic64/Heartfelt-Gold/releases/download/heartfelt-v1.0.10/Heartfelt-Gold-v1.0.10-Patch.xdelta).
- [Open the v1.0.10 guide online](https://trinsic64.github.io/Heartfelt-Gold/).
- [Download the offline guide ZIP](https://github.com/Trinsic64/Heartfelt-Gold/releases/download/heartfelt-v1.0.10/Heartfelt-Gold-Player-Guide-Offline.zip), extract it, then double-click `index.html`. Keep the extracted files together so the Rematch Trainers link works. No installation or internet connection is needed after downloading.
- [Download the checksums file](https://github.com/Trinsic64/Heartfelt-Gold/releases/download/heartfelt-v1.0.10/RELEASE-CHECKSUMS-HEARTFELT-v1.0.10.sha256) to verify both downloads.

The guide includes story chapters, the Trainer tab, separate rematch trainers, wild encounters, items, marts, evolutions and static encounters. Gym chapters show their regular trainers before the Leader and the Leader's bonus battle. The HTML pages include their sprites and can be searched, enlarged and printed.

## Apply the patch

Use a legally obtained, clean **Pokémon HeartGold (USA)** ROM with SHA-256 `65f02a56842b75aa92d775d56d657a56fe3fa993550b04dc20704ab82d760105`. Apply `Heartfelt-Gold-v1.0.10-Patch.xdelta` to that clean ROM using an xDelta patcher. Apply one patch to the clean ROM; do not stack it over an earlier Heartfelt Gold version.

Back up your in-game save before switching versions. A copied save loaded and reached gameplay in a headless v1.0.10 emulator check. A new save/reload test and full playthrough were not performed. Use the in-game save rather than an emulator save state from an older ROM.

## Build and verification

| Artifact | Size | SHA-256 |
| --- | ---: | --- |
| v1.0.10 xDelta patch | 39,296,010 bytes | `2f20d3092ba208ffd0c24dbe437801ca017674f8a86d4160f926041c99c36ad2` |
| Offline guide ZIP | 3,677,457 bytes | `324be5adbd905a1c0bbb3267221754e6c8bc09070581cf7ce944c58686dcdb58` |
| Decoded ROM (verification only; not distributed) | 207,711,200 bytes | `5173570c76d8e333f19cfebd9671f7242990aae8ccd1bfe3f711f9114c623298` |

The patch decoded against the documented clean USA source and matched the v1.0.10 hg-engine build byte for byte. The build's port audit passed checks for protected project sources, configuration, ROM data, messages, scripts, items, headers and cameras. A headless DeSmuME check reached gameplay from a copied save. The engine source commit is `23c4f1ab256ace92bcba4585df3c0b2959741676`.

The supplied v22 test input SHA-256 was `cab62a140eef13bb66b46539ce7f4816859392f8b1345b8ad497acfe5ebbb833`. The [guide release record](Docs/Player-Guide/release.json) keeps the input, build, patch and guide version together.

The guide uses the current engine authoring data and the named Release-v2 event and script extraction. Two visible pickup objects still have unresolved item identities. Scripted encounter listings and parent-area warps do not prove reachability or unlock conditions; individual guide rows have not all been checked in gameplay. See the [guide review notes](Docs/Player-Guide/site/README-CSV-Review.md).

Only the patch and guide are distributed. No ROM or save is included.
