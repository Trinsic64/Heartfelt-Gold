# Heartfelt Gold player guide notes — v1.0.11

Open `index.html` locally, or use the published guide at https://trinsic64.github.io/Heartfelt-Gold/. The two HTML pages include their sprites, styles, and code. Rematches have a separate page; bonus battles stay with story trainers.

This guide is bundled with the v1.0.11 patch named in `release.json`. The patch was decoded against the documented clean USA ROM and matched the recorded hg-engine build hash.

The trainer, wild encounter, shop, and evolution tables reflect the current authoring data used for this guide. Wild held items match the v1.0.11 `HG-Engine/data/Species.c` snapshot, including form-specific rows. Ground pickups come from the named Release-v2 event extraction and hidden item parameter table. Two visible pickup objects have unresolved item identities. The 89 static encounter rows use v22 Test levels and follow the reviewed Markdown guide; the unbound Union Cave Victini command is excluded. Parent areas are traced through inbound warps or bound same-map event objects; script and placement data do not by themselves establish reachability or unlock conditions. Individual guide rows have not all been independently checked against gameplay.

See `Release-v22-Item-Audit.md` for the item audit. `Item-Locations.csv` is the older Retiled Expansion item list and remains historical. Form-specific encounter rows and evolution icons were resolved against engine species IDs.
