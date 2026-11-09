# Pokémon Heartfelt Gold v1.0.12

This release uses the v23 Test map input and the latest HGEFE trainer, shop, and evolution edits. It includes the Diglett's Cave missing-map fix. The online guide, offline guide, and CSV tables have been updated for the same build.

## Downloads and guide

- [Download the v1.0.12 xDelta patch](https://github.com/Trinsic64/Heartfelt-Gold/releases/download/heartfelt-v1.0.12/Heartfelt-Gold-v1.0.12-Patch.xdelta).
- [Open the v1.0.12 guide online](https://trinsic64.github.io/Heartfelt-Gold/).
- [Download the offline guide ZIP](https://github.com/Trinsic64/Heartfelt-Gold/releases/download/heartfelt-v1.0.12/Heartfelt-Gold-Player-Guide-Offline.zip), extract it, then double-click `index.html`. Keep the extracted files together so the Rematch Trainers link works.
- [Download checksums for both files](https://github.com/Trinsic64/Heartfelt-Gold/releases/download/heartfelt-v1.0.12/RELEASE-CHECKSUMS-HEARTFELT-v1.0.12.sha256).

## What changed

- The v23 map input supplies Diglett's Cave map ID 976 and updates matrix 2 to reference it. Both map archives in the output match the v23 input byte for byte.
- The game includes HGEFE trainer party edits. Compared with v1.0.11, 21 player-facing trainer party IDs changed; the trainer CSV, story guide, and Trainer Guide Markdown now show those teams in gameplay chapter order, with gym trainers before their leader and bonus battle.
- Cherrygrove Mart now lists Cherish Ball. Both Frillish evolution entries now use level 40 without a gender condition.
- Wild held items carry forward from the updated `Species.c`. The 89 scripted encounter levels carry forward from the reviewed v22 Test script guide. The ground pickup audit remains based on the named Release-v2 event extraction.

## Apply the patch

Use a legally obtained, clean **Pokémon HeartGold (USA)** ROM with SHA-256 `65f02a56842b75aa92d775d56d657a56fe3fa993550b04dc20704ab82d760105`. Apply `Heartfelt-Gold-v1.0.12-Patch.xdelta` directly to that clean ROM using an xDelta patcher. Do not apply it over v1.0.11 or any other patched ROM.

Back up your in-game save before switching versions. A copied save loaded and reached gameplay in a v1.0.11 headless emulator check. v1.0.12 has not received a new save/reload test or a full playthrough. Use the in-game save rather than an emulator save state from an older ROM.

## Build and verification

| Artifact | Size | SHA-256 |
| --- | ---: | --- |
| v1.0.12 xDelta patch | 39,309,089 bytes | `f7d6e78332db8629d4f4099af1dbba5846c3acc155a79894a1252dd2e8a215ba` |
| Offline guide ZIP | 4,785,793 bytes | `0745a6aa87a7c62e71d089b01980dedbb26e79fb52889cbd49f2aea1497df121` |
| Decoded ROM (verification only; not distributed) | 207,742,432 bytes | `9f6e08223717ad90dbf3ce281aed2410c2e209f1e53ed5a566eb79f41bc3731a` |

The patch decoded against the documented clean USA source and matched the v23 hg-engine build byte for byte. The guide's [release manifest](Docs/Player-Guide/release.json) records the source snapshots and hashes used for this version. The v23 map fix was checked in the map archive and matrix; in-game cave navigation has not been separately verified. Script listings do not establish encounter reachability or unlock conditions. Two visible ground pickup objects remain unresolved in the [item audit](Docs/Player-Guide/site/Release-v22-Item-Audit.md).

**Guide correction:** The eight-badge Elite Four and Champion run is separate from the postgame run after Gym #16 Blue. The five second-run teams and their five bonus battles appear together in the postgame chapter and trainer list. The game patch is unchanged.

**Gym order correction:** Every Gym chapter now lists its Gym Trainers in audited order, then the Leader, then the Leader's Bonus Battle in both the walkthrough and Trainers tab. The guide builder checks this order in the HTML data and CSV before publishing.

**Mega form display:** Trainer cards now use the in-battle Mega sprite, ability, and typing for 500 Pokémon across story, bonus, and rematch teams. This display is resolved from the build's Mega Stone, form, and species tables, including Rayquaza's Dragon Ascent form. The trainer CSV retains the base party data, and wild encounters are unchanged. Four Tatsugiri with Tatsugirinite and Blue's Floette with Floettite retain their base display because their configured target forms do not resolve to Mega species in this build. The game patch is unchanged.

**Mart guide update.** The Marts tab has 30 sidebar tabs across 21 shop locations. Each department store floor or named counter has its own stock table. TM numbers show the move they teach. All 1,065 stock rows use prices from the build's `itemdata.c`.

**Pokédex.** Compare species and forms in a searchable table with sortable National Pokédex numbers, names, and stats. Open an entry to see its battle sprite and full profile. Machine learnsets display TM001–TM092 and HMs.

Only the patch and guide are distributed. No ROM or save is included.
