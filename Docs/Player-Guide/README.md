# Heartfelt Gold player guide — v1.0.15

**For players:** [Open the guide online](https://trinsic64.github.io/Heartfelt-Gold/). It includes the story walkthrough, Pokédex, trainer chapters, wild encounters, shops, item locations, evolutions, and scripted encounters. [Separate rematch guide](https://trinsic64.github.io/Heartfelt-Gold/Rematch-Trainer-Guide.html).

**For offline play:** Download the ZIP, extract it, and double-click `index.html`. For rematches, open `Rematch-Trainer-Guide.html` in the same folder. Both pages include their sprites, styles, and code and work offline. [Download the v1.0.15 offline ZIP](https://github.com/Trinsic64/Heartfelt-Gold/releases/download/heartfelt-v1.0.15/Heartfelt-Gold-Player-Guide-Offline.zip).

The standalone HTML also opens locally by itself. To use it from GitHub, download the file and open it in your browser. [Standalone index.html](site/index.html).

This guide covers both v1.0.15 camera patches in [release.json](release.json). Both reproduce their v31 builds byte for byte. The walkthrough and trainer CSVs use the revised Ariana, Team Rocket Grunt, and Falkner bonus parties. The Pokédex uses the current move pools, expanded tutor roster, and updated hidden abilities. The guide also lists the revised evolutions, all three Burmy cloaks in Route 33 Headbutt trees, Syrupy Apple at Goldenrod Department Store, and the two Suicune script entries. Ground pickups retain the reviewed v22 evidence. [Source and review notes](site/README-CSV-Review.md).

The first Elite Four and Champion run appears after eight badges. The second run and its bonus battles have their own postgame chapter after Gym #16 Blue; the five second-run teams are included on the main trainer page rather than the generic rematch page.

The scripted trainer audit verifies the release ROM's battle commands and map associations. The guide separates the two Dance Theater visits, gives Team Rocket HQ its own Trainer chapter, and shows Gym rematches at the Saffron Fighting Dojo. See the [scripted trainer audit](site/Scripted-Trainer-Audit.md).

Every Gym chapter lists its Gym Trainers in audited order, then the Leader, then the Leader's Bonus Battle. This applies to the walkthrough and Trainers tab. The bundle builder checks the HTML and CSV order before publishing; after changing trainer data, run `python Docs/Player-Guide/order-gym-trainers.py --source "C:\ROM-Hack\Heartfelt-Gold\Docs"` before rebuilding.

Trainer cards show in-battle Mega form sprites, abilities, and types when the build's Mega Stone and form tables resolve a Mega species. This applies to story, bonus, and rematch trainers; wild encounter display is unchanged. The trainer CSV keeps the base species and ability stored in the ROM. Four Tatsugiri with Tatsugirinite and Blue's Floette with Floettite retain their base display because the current engine form table does not resolve those entries to Mega species. To refresh after trainer or Mega data changes, run `python Docs/Player-Guide/add-trainer-mega-forms.py --source "C:\ROM-Hack\Heartfelt-Gold\Docs"` before building the standalone guide. Pass `--engine-sprites "<hg-engine>/data/graphics/sprites"` when new forms need to be copied into the versioned asset set.

The site is published from `Docs/Player-Guide/site` by the [Pages workflow](../../.github/workflows/player-guide-pages.yml). To regenerate the portable pages from a reviewed guide export, run:

```powershell
python Docs/Player-Guide/add-mart-prices.py --source "C:\ROM-Hack\Heartfelt-Gold\Docs"
python Docs/Player-Guide/build-standalone.py --source "C:\ROM-Hack\Heartfelt-Gold\Docs"
```

The build script checks that every referenced sprite exists, embeds them once per page, and creates the offline ZIP from the same pages. Its versioned [app script](Guide-App.js) and [style](Guide-Style.css) must match the reviewed export, so guide behavior changes are included in the same repository change as the generated pages.

The Marts page has 30 tabs across 21 locations. Each department store floor or named counter has its own stock table. TMs show the move name next to the number and can be searched by either. Prices and move names come from the build's item and move data.

The Pokédex is generated when the standalone guide is built. Its searchable table sorts by National Pokédex number, name, or base stats. Forms share their base species' number, and Ability 3 shows the hidden ability. Each entry has a battle sprite, species data, and level, TM/HM, egg, and tutor moves. The guide displays TM001–TM092 and HMs from the full engine machine learnset. When a release updates species, forms, abilities, moves, or learnsets, refresh the corresponding `HG-Engine` snapshots before rebuilding. If the export is missing battle sprites, run `python Docs/Player-Guide/pokedex-data.py --source "C:\ROM-Hack\Heartfelt-Gold\Docs" --engine-sprites "<hg-engine>/data/graphics/sprites"`. See [Pokédex data extractor](pokedex-data.py).

For each release, update `release.json` with both camera patch paths and verified hashes, rebuild the guide, and run `python Docs/Player-Guide/verify-release-pair.py`. The Pages workflow runs the same check before publishing the guide.
