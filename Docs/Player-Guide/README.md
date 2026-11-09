# Heartfelt Gold player guide — v1.0.12

**For players:** [Open the guide online](https://trinsic64.github.io/Heartfelt-Gold/). It includes the story walkthrough, trainer chapters, wild encounters, shops, item locations, evolutions, and scripted encounters. Rematch trainers have a separate page linked from the guide.

**For offline play:** [Download the v1.0.12 offline ZIP](https://github.com/Trinsic64/Heartfelt-Gold/releases/download/heartfelt-v1.0.12/Heartfelt-Gold-Player-Guide-Offline.zip), extract it, and double-click `index.html` in the extracted folder. Keep both HTML pages together so **Open rematch trainers** works. The pages contain their own sprites, styles, and code; no installation or internet connection is needed after downloading.

The [standalone `index.html`](site/index.html) also opens locally by itself. Download both HTML pages if you want the rematch link to work without the ZIP. GitHub's file preview shows HTML source rather than running the guide; open the published site or download the files.

This guide is paired with the v1.0.12 patch in [release.json](release.json). The patch was decoded against the documented clean source and matched the v23 build byte for byte. Trainer parties, the Cherrygrove Mart, and Frillish evolutions reflect the v23 data. Wild held items use the updated [Species.c snapshot](../../HG-Engine/data/Species.c); the 89 scripted encounters use the reviewed v22 Test levels. Ground pickups were audited from the named Release-v2 event extraction, with two unresolved visible objects. Scripted encounters and listed placements do not by themselves establish reachability or unlock conditions; individual guide rows have not all been checked in gameplay. See [source and review notes](site/README-CSV-Review.md) and the [item audit](site/Release-v22-Item-Audit.md).

The first Elite Four and Champion run appears after eight badges. The second run and its bonus battles have their own postgame chapter after Gym #16 Blue; the five second-run teams are included on the main trainer page rather than the generic rematch page.

Every Gym chapter lists its Gym Trainers in audited order, then the Leader, then the Leader's Bonus Battle. This applies to the walkthrough and Trainers tab. The bundle builder checks the HTML and CSV order before publishing; after changing trainer data, run `python Docs/Player-Guide/order-gym-trainers.py --source "C:\ROM-Hack\Heartfelt-Gold\Docs"` before rebuilding.

Trainer cards show in-battle Mega form sprites, abilities, and types when the build's Mega Stone and form tables resolve a Mega species. This applies to story, bonus, and rematch trainers; wild encounter display is unchanged. The trainer CSV keeps the base species and ability stored in the ROM. Four Tatsugiri with Tatsugirinite and Blue's Floette with Floettite retain their base display because the current engine form table does not resolve those entries to Mega species. To refresh after trainer or Mega data changes, run `python Docs/Player-Guide/add-trainer-mega-forms.py --source "C:\ROM-Hack\Heartfelt-Gold\Docs"` before building the standalone guide. Pass `--engine-sprites "<hg-engine>/data/graphics/sprites"` when new forms need to be copied into the versioned asset set.

The site is published from `Docs/Player-Guide/site` by the [Pages workflow](../../.github/workflows/player-guide-pages.yml). To regenerate the portable pages from a reviewed guide export, run:

```powershell
python Docs/Player-Guide/add-mart-prices.py --source "C:\ROM-Hack\Heartfelt-Gold\Docs"
python Docs/Player-Guide/build-standalone.py --source "C:\ROM-Hack\Heartfelt-Gold\Docs"
```

The build script checks that every referenced sprite exists, embeds them once per page, and creates the offline ZIP from the same pages. Its versioned [app script](Guide-App.js) and [style](Guide-Style.css) must match the reviewed export, so guide behavior changes are included in the same repository change as the generated pages. The Marts page has 27 shop and floor tabs across 21 locations. Each department store floor has its own sidebar tab and priced table; counters on the same floor appear together. Item prices come from the [item data snapshot](../../HG-Engine/data/itemdata/itemdata.c).

For each release, update `release.json` with the patch filename and verified hashes, rebuild the guide, and run `python Docs/Player-Guide/verify-release-pair.py`. The Pages workflow runs the same check before publishing the guide.
