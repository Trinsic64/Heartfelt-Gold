# Scripted trainer audit for Heartfelt Gold v1.0.12

Reviewed the v23 release ROM (`9f6e08223717ad90dbf3ce281aed2410c2e209f1e53ed5a566eb79f41bc3731a`). Its 1,139 script banks, 578 event members, and 627 map headers match both DSPRE extracts byte for byte. The v22 script text supplied the disassembly.

Found 186 battle references in the disassembly of 51 banks. All 134 distinct literal party IDs are present in the story or rematch guide. Alternate cutscene paths and shared script offsets can repeat a party reference. Bank 0953 uses variables for ordinary overworld trainers. The Victoria call in common bank 0003 has no direct map header, so her regular Goldenrod Gym placement is used.

## Progression checks

- **Team Rocket HQ.** Headers 247–249 bind B1F–B3F. The B1F alarm scripts call Grunts 223 and 224. Nine additional parties are bound to trainer objects across the three floors. Petrel is on B3F. The B2F generator-door battle calls Ariana and Grunt 499 with Lance 675 as the player’s partner. The group follows the route through the base. Optional trainer order can vary.
- **Ecruteak Dance Theater.** Header 86 and bank 0928 bind both visits. Script 4 calls Grunt 601 on the first visit. The later branches all call Zuki → Naoko → Miki → Sayo → Kuni. The dialogue refers to completing the Dragon’s Den test and defeating Team Rocket in Goldenrod. The guide places the five battles after the eight Johto badges, before Routes 26–27.
- **Goldenrod takeover.** The Radio Tower and Goldenrod Tunnel B2F/Warehouse trainers appear in the raid after Pryce. The scripted parties include Petrel, Silver’s three starter variants, and Archer.
- **Silver follow-up.** Mt. Moon bank 0007 sets `0x40FC` to 1. The Dragon’s Den tag-battle trigger uses that state and its win sets it to 2. League entrance bank 0819 checks that progression and weekday values 1 or 3. These follow-up battles are grouped with the Mt. Moon stage, with the actual battle locations shown on the cards.
- **Gym rematches.** Bank 0832 (header 398) calls all 16 Gym rematch teams at the Saffron Fighting Dojo. The rematch CSV and HTML show the Dojo and keep each team's original Gym stage for reference.

The audit confirms the script operands and map associations. Conditional branches and optional events were read from source, and the audit did not play through every trigger.

## Field script inventory

| Bank | Map header and area | Opponent IDs | Partner IDs |
| --- | --- | --- | --- |
| 0003 | Common / no direct map header | 5 | — |
| 0007 | 107 Mt. Moon (D02R0101) | 285, 286, 287 | — |
| 0015 | 457 Seafoam Islands (D11R0106) | 259, 689, 690, 691, 692, 693, 694, 757 | — |
| 0018 | 156 Sprout Tower (D15R0103) | 290 | — |
| 0023 | 7 Burned Tower (D18R0101) | 263, 267, 270 | — |
| 0029 | 112 Radio Tower (D23R0101) | 185 | — |
| 0032 | 188 Radio Tower (D23R0104) | 200 | — |
| 0033 | 189 Radio Tower (D23R0105) | 487 | — |
| 0034 | 190 Radio Tower (D23R0106) | 485 | — |
| 0060 | 177 SLOWPOKE Well (D26R0102) | 486 | — |
| 0089 | 247 Team Rocket HQ (D35R0102) | 223, 224 | — |
| 0090 | 248 Team Rocket HQ (D35R0103) | 479, 499 | 675 |
| 0091 | 249 Team Rocket HQ (D35R0104) | 488 | — |
| 0096 | 201 Goldenrod City (D37R0104) | 271, 288, 289 | — |
| 0098 | 252 Mt. Mortar (D38R0104) | 158 | — |
| 0107 | 465 Mt. Silver Cave (D41R0108) | 260 | — |
| 0110 | 179 Victory Road (D43R0103) | 264, 268, 272 | — |
| 0111 | 253 Dragon’s Den (D44R0102) | 733, 734 | 735, 736, 737 |
| 0114 | 298 Tohjo Falls (D45R0102) | 700 | — |
| 0158 | 309 S.S. Aqua (P01R0303) | 238 | — |
| 0215 | 28 Route 24 (R24) | 353 | — |
| 0216 | 29 Route 25 (R25) | 361 | — |
| 0237 | 38 Route 34 (R34) | 118, 120, 417 | — |
| 0743 | 496 Viridian City (T02GYM0101) | 261, 758 | — |
| 0752 | 473 Pewter City (T03GYM0101) | 253, 751 | — |
| 0760 | 427 Cerulean City (T04GYM0101) | 254, 752 | — |
| 0778 | 365 Vermilion City (T06GYM0101) | 255, 753 | — |
| 0786 | 395 Celadon City (T07GYM0101) | 256, 754 | — |
| 0809 | 480 Fuchsia City (T08GYM0101) | 83, 84, 136, 183, 257, 755 | — |
| 0819 | 300 Pokémon League (T10R0101) | 489, 490, 491 | — |
| 0820 | 301 Pokémon League (T10R0201) | 245, 702, 746, 759 | — |
| 0821 | 302 Pokémon League (T10R0301) | 247, 703, 747, 760 | — |
| 0822 | 303 Pokémon League (T10R0401) | 418, 704, 748, 761 | — |
| 0823 | 304 Pokémon League (T10R0501) | 246, 705, 749, 762 | — |
| 0824 | 305 Pokémon League (T10R0601) | 244, 701, 750, 763 | — |
| 0829 | 410 Saffron City (T11GYM0101) | 258, 756 | — |
| 0832 | 398 Saffron City (T11R0101) | 712, 713, 714, 715, 716, 717, 718, 719, 720, 721, 722, 723, 724, 725, 726, 727 | — |
| 0850 | 67 Cherrygrove City (T21) | 495, 496, 497 | — |
| 0859 | 135 Violet City (T22GYM0101) | 20, 738 | — |
| 0866 | 74 Azalea Town (T23) | 1, 266, 269 | — |
| 0869 | 180 Azalea Town (T23GYM0102) | 21, 739 | — |
| 0875 | 75 Cianwood City (T24) | 498 | — |
| 0877 | 139 Cianwood City (T24GYM0101) | 34, 742 | — |
| 0886 | 137 Goldenrod City (T25GYM0101) | 30, 740 | — |
| 0913 | 138 Olivine City (T26GYM0101) | 33, 743 | — |
| 0914 | 226 Olivine City (T26PC0101) | 728 | — |
| 0922 | 80 Ecruteak City (T27GYM0101) | 31, 741 | — |
| 0928 | 86 Ecruteak City (T27R0501) | 160, 161, 162, 163, 164, 601 | — |
| 0932 | 140 Mahogany Town (T28GYM0101) | 32, 744 | — |
| 0943 | 141 Blackthorn City (T30GYM0101) | 35, 745 | — |
| 0953 | Common / no direct map header | variable `0x8004`, variable `0x8005` | — |
