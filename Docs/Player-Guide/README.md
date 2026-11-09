# Heartfelt Gold player guide

**For players:** [Open the guide online](https://trinsic64.github.io/Heartfelt-Gold/). It includes the story walkthrough, trainer chapters, wild encounters, shops, item locations, evolutions, and scripted encounters. Rematch trainers have a separate page linked from the guide.

**For offline play:** [Download the offline ZIP](https://trinsic64.github.io/Heartfelt-Gold/Heartfelt-Gold-Player-Guide-Offline.zip), extract it, and double-click `index.html`. The guide pages contain their own sprites, styles, and code; no installation or internet connection is needed after downloading.

The [standalone `index.html`](site/index.html) also opens locally by itself. Download both HTML pages if you want the rematch link to work without the ZIP. GitHub's file preview shows HTML source rather than running the guide; open the published site or download the files.

The guide reflects current authoring data for trainers, wild encounters, evolutions, and shops. Ground pickups were audited from the named Release-v2 event extraction, with two unresolved visible objects. Scripted encounters and listed placements do not by themselves establish in-game reachability or unlock conditions. The repository's currently released patch has not been independently checked against every guide table. See [source and review notes](site/README-CSV-Review.md) and the [item audit](site/Release-v22-Item-Audit.md).

The site is published from `Docs/Player-Guide/site` by the [Pages workflow](../../.github/workflows/player-guide-pages.yml). To regenerate the portable pages from a reviewed guide export, run:

```powershell
python Docs/Player-Guide/build-standalone.py --source "C:\ROM-Hack\Heartfelt-Gold\Docs"
```

The build script checks that every referenced sprite exists, embeds them once per page, and creates the offline ZIP from the same pages.
