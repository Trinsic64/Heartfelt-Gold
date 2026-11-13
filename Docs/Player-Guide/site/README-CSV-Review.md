# Heartfelt Gold player guide notes — v1.0.15

Open `index.html` locally, or use the published guide at https://trinsic64.github.io/Heartfelt-Gold/. The two HTML pages include their sprites, styles, and code. Rematches have a separate page; bonus battles stay with story trainers. The first Elite Four and Champion run follows eight badges, while the second run and its bonus battles follow Gym #16 Blue.

This guide covers both v1.0.15 camera variants in `release.json`. Each patch decoded against the documented clean USA ROM and matched its hg-engine build hash.

The trainer tables include 3 party changes from the v1.0.13 guide. The trainer tables use the compiled trainer archives and the matching `HG-Engine/data/Trainers.c` source. Internal dummy Trainer 0 is omitted. See `Scripted-Trainer-Audit.md` for battle placements and cap evidence. Goldenrod Department Store stocks Syrupy Apple, and Route 33 Headbutt includes all three Burmy cloaks. Wild held items match the updated `HG-Engine/data/Species.c` snapshot, including form-specific rows. Ground pickups come from the named Release-v2 event extraction and hidden item parameter table. Two visible pickup objects have unresolved item identities. Static encounter levels follow the reviewed Markdown guide, including the v31 Suicune events. The unbound Union Cave Victini command is excluded. Parent areas are traced through inbound warps or bound same-map event objects; script and placement data do not by themselves establish reachability or unlock conditions. Individual guide rows have not all been independently checked against gameplay.

Trainer cards show the in-battle Mega sprite, ability, and typing where the build's Mega Stone/form tables resolve a Mega species; the trainer CSV keeps the base party species stored in the ROM. Four Tatsugiri with Tatsugirinite and Blue's Floette with Floettite retain their base display because the configured target forms do not resolve to Mega species in this build.

Mart stock rows show the price from the build's itemdata.c. The Mart atlas groups 31 counters into 30 tabs across 21 locations. Department store floors and named counters have separate tabs. Machine move names come from the engine's `MachineMoves.c` and `Moves.c`. Prices have not been independently checked against an in-game purchase.

The Pokédex uses the engine's species, ability, and learnset tables. Forms use the engine's learnset inheritance rules. Machine and tutor lists reflect compatibility in the build.

See `Release-v22-Item-Audit.md` for the item audit. `Item-Locations.csv` is the older Retiled Expansion item list and remains historical. Form-specific encounter rows and evolution icons were resolved against engine species IDs. The v31 build includes dynamic cameras and retains the two Camera 0 options.
