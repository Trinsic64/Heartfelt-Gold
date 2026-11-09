# Release v22 item audit

Read-only audit of the named Release-v2 DSPRE extraction. It does not establish that every item is reachable during normal play.

- 578 event files, 627 map headers, 1139 expanded script banks read.
- 244 visible item object rows and 174 hidden item rows across map headers.
- 59 script sections with an item-grant helper or direct item command.
- 5 interaction sections are bound to placed ground objects; the others have no verified placement binding.
- 2 placed item object rows have no confirmed item identity.

Visible item balls with script numbers 7000–7999 encode the item ID. Hidden pickups use the installed hidden-item table in `files/a/0/2/8`, member 18. Local scripts were checked for item variables and `CommonScript 2001`. Reused event files can produce multiple map-header rows.

## Unresolved placed objects

- Event 0017, header 20, script bank 0199, entry 7: no direct item grant found at that entry.
- Event 0036, header 39, script bank 0240, entry 6: no direct item grant found at that entry.

## Static encounter parent areas

Parent areas come from direct inbound event warps to the encounter's map header. A missing warp is explicitly marked; script teleports and unlock conditions were not inferred.

## Outputs

- `Release-v22-Ground-Pickups.csv`: map-bound visible and hidden pickups.
- `Release-v22-Script-Item-Interactions.csv`: item-grant script sections, with binding status.
- `Static-Encounters.csv`: includes parent area and link evidence.
- `Item-Locations.csv`: historical guide retained separately.
