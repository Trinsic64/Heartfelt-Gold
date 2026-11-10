# Heartfelt Gold gameplay features

This page reflects the current hg-engine authoring configuration supplied for Pokémon Heartfelt Gold. The release patch has not been independently decoded to confirm every setting.

## Start and progression

- The three starter choices are Treecko, Torchic, and Mudkip. The starter creation code gives each its matching Mega Stone.
- The National Dex is configured to be available from the start.
- Mega Evolution is configured in the engine. The existing Oak event is the documented Mega Ring source.
- The v1.0.13 Gym and League victory scripts update the EXP level cap while its current value is below 100. The values below come from the released scripts. [Scripted trainer audit](../Player-Guide/site/Scripted-Trainer-Audit.md).

| Victories | Level cap after each victory |
| --- | --- |
| Falkner, Bugsy, Whitney, Morty | 24, 29, 34, 38 |
| Chuck, Jasmine, Pryce, Clair | 42, 45, 50, 65 |
| First League run through Will, Koga, Bruno, Karen, and Lance | 67, 68, 70, 70, 72 |
| Lt. Surge, Sabrina, Misty, Erika, Janine, Brock, Blaine, and Blue | 74, 76, 78, 80, 82, 84, 86, 94 |
| Postgame Karen, then postgame Lance | 98, 100 |

## Quality of life

| Feature | Current source setting |
| --- | --- |
| TMs | Reusable |
| HMs | Can be forgotten |
| Frame rate | Uncapped in the overworld and battles |
| Text speed | Instant text is not forced |
| Marts | Expanded stock, including evolution items, specialty Poké Balls, and selected Mega Stones |

The [Evolution Guide](Evolution-Guide.md) lists the current configured methods, and the [Static Encounter Guide](Static-Encounter-Guide.md) lists scripted species and levels from the supplied DSPRE export. Shop inventories are defined in [mart.c](../../HG-Engine/src/field/mart.c); some entries can depend on story state.

The [Wild Encounter Guide](Wild-Encounter-Guide.md) and [Trainer Guide](Trainer-Guide.md) are generated from the current encounter and trainer tables. Online services, Pokéwalker dependencies, and Pal Park migration are not documented as restored by these changes.
