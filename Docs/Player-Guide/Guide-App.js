(() => {
  "use strict";
  const DATA = window.GUIDE_DATA;
  const REMATCH = DATA.mode === "rematch";
  const shopTabsByKey = new Map();
  for (const shop of DATA.shops || []) {
    const floor = shop.name.includes("Department Store") ? shop.floor : "";
    const key = floor ? `${shop.name}::${floor}` : shop.name;
    if (!shopTabsByKey.has(key)) shopTabsByKey.set(key, { key, label: floor ? `${shop.name} · ${floor}` : shop.name, counters: [] });
    shopTabsByKey.get(key).counters.push(shop);
  }
  const shopTabs = [...shopTabsByKey.values()];
  const pokedex = DATA.pokedex?.pokemon || [];
  const machineMoves = DATA.pokedex?.machineMoves || {};
  const state = { view: REMATCH ? "rematches" : "walk", chapter: 1, trainerGroup: "All", shopLocation: shopTabs[0]?.key || "", filter: "All", page: 0, query: "", locationQuery: "", selectedArea: -1 };
  let selectedPokemon = null;
  let dexListScroll;
  const dexSort = { column: "number", direction: 1 };
  const PAGE = 8;
  const WILD_PAGE = 6;
  const $ = id => document.getElementById(id);
  const esc = value => String(value ?? "").replace(/[&<>"']/g, ch => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[ch]));
  const icon = (src, cls = "small-sprite", alt = "", lazy = false) => src ? `<img class="${cls}" src="${esc(src.startsWith("Sprites/Items/") ? src + "?v=2" : src)}" alt="${esc(alt)}"${lazy ? ' loading="lazy"' : ""}>` : "";
  const chapterNum = value => Number.parseInt(String(value).slice(0, 2), 10) || 45;
  // Keep audited Gym Trainer order, then the Leader, then the Bonus Battle.
  const gymRank = trainer => trainer.bonus ? 2 : trainer.major ? 1 : 0;
  const gymOrder = (a, b) => a.group === b.group && a.group?.startsWith("gym-") ? gymRank(a) - gymRank(b) : 0;
  const matches = (values, q = state.query) => !q || values.some(v => String(v ?? "").toLocaleLowerCase().includes(q));
  const title = (text, count = "") => `<h2>${esc(text)}${count === "" ? "" : `<small>${count} ${count === 1 ? "entry" : "entries"}</small>`}</h2>`;
  const notice = (text, blue = false) => `<div class="notice${blue ? " blue" : ""}">${esc(text)}</div>`;
  const stats = (...values) => `<div class="stats">${values.map(([n, label]) => `<span class="stat"><strong>${esc(n)}</strong> ${esc(label)}</span>`).join("")}</div>`;
  const chip = text => `<span class="badge">${esc(text)}</span>`;
  const price = value => Number.isFinite(value) ? `₽${value.toLocaleString("en-US")}` : "Price unavailable";
  const itemLabel = name => Object.hasOwn(machineMoves, name) ? `${name} · ${machineMoves[name]}` : name;
  const shopItemMatches = (item, floor) => matches([itemLabel(item.name), floor, item.price, item.badges]);
  const imageName = obj => obj.front
    ? `<span class="front-sprite" aria-hidden="true" style="background-image:url('${esc(obj.front)}')"></span>`
    : `${icon(obj.icon, "mon-icon")}${!obj.icon ? '<span class="mon-icon placeholder" aria-hidden="true">◈</span>' : ""}`;

  function typeChips(types) {
    if (!types?.length) return "";
    return `<div class="types">${types.map(t => `<span class="type ${esc(t.toLowerCase())}">${esc(t)}</span>`).join("")}</div>`;
  }

  function trainerCard(t) {
    const portrait = t.portrait
      ? `<div class="portrait-window" aria-hidden="true" style="background-image:url('${esc(t.portrait)}');background-size:224px 112px;background-position:left center;background-repeat:no-repeat"></div>`
      : `<div class="portrait-window" aria-hidden="true"><span class="portrait-fallback">♟</span></div>`;
    const team = t.team.map(m => {
      const shown = m.mega || m;
      return `<div class="mon-card">
      <div class="mon-top">${imageName(shown)}<div><div class="mon-name">${esc(shown.name)}</div><div class="level">Lv. ${esc(m.level)}${m.mega ? " · Mega form" : ""}</div></div></div>
      ${typeChips(shown.types)}<div class="ability"><strong>Ability:</strong> ${esc(shown.ability)}${m.mega ? ' <span class="ability-kind">(Mega)</span>' : m.abilitySlot === "Hidden" ? ' <span class="ability-kind">(Hidden)</span>' : ""}</div><div class="held"><strong>Held:</strong> ${icon(m.heldSprite, "small-sprite")}<span>${esc(m.held || "No held item")}</span></div>
      <div class="moves">${m.moves.length ? m.moves.map(move => `<span class="move">${esc(move)}</span>`).join("") : `<span class="move dim">Moves not listed</span>`}</div>
    </div>`;
    }).join("");
    const badges = [t.major ? '<span class="badge major">Major battle</span>' : "", t.bonus ? '<span class="badge bonus">Bonus battle</span>' : "", t.rematch ? '<span class="badge rematch">Rematch</span>' : ""].join("");
    const rematchText = t.rematch ? `${esc(t.rematchInfo.kind)} · ${esc(t.rematchInfo.variant)} · original ID ${esc(t.rematchInfo.base)}` : "";
    const battleItems = t.battleItemIcons?.length ? `<span class="battle-items">${t.battleItemIcons.map(i => `<span>${icon(i.sprite, "small-sprite", i.name)} ${esc(i.name)}</span>`).join("")}</span>` : "None listed";
    return `<article class="trainer-card" id="trainer-${esc(t.id)}"><div class="trainer-heading"><div><h3>${esc(t.name)} <span class="dim">· ${esc(t.class)}</span></h3><div class="sub">${esc(t.location === "—" ? "Location not resolved" : t.location)}${rematchText ? " · " + rematchText : ""}</div></div><div class="badges">${badges}</div></div>
      <div class="trainer-body"><div class="trainer-side">${portrait}<div><div class="trainer-class">${esc(t.class)}</div><div class="trainer-id">Trainer ID ${esc(t.id)}</div></div></div><div class="team-grid">${team}</div></div>
      <div class="trainer-foot"><strong>Battle items:</strong> ${battleItems}${t.bonusNote ? ` · <strong>Source note:</strong> ${esc(t.bonusNote)}` : ""}</div></article>`;
  }

  function methodKind(method) {
    if (method === "Grass") return "";
    if (["Surf", "Old Rod", "Good Rod", "Super Rod"].includes(method)) return "water";
    if (["Rock Smash", "Headbutt"].includes(method)) return "rock";
    return "conditional";
  }
  function methodIcon(method) {
    return ({ Grass: "🌿", Surf: "🌊", "Old Rod": "🎣", "Good Rod": "🎣", "Super Rod": "🎣", Headbutt: "🌳", "Rock Smash": "🪨" })[method] || "✦";
  }
  function areaCard(area, filtered = null) {
    const entries = filtered || area.entries;
    const groups = new Map();
    for (const e of entries) {
      const key = `${e.method}|${e.condition || ""}|${e.time}`;
      if (!groups.has(key)) groups.set(key, []);
      groups.get(key).push(e);
    }
    const blocks = [...groups.values()].map(group => {
      const sample = group[0], kind = methodKind(sample.method);
      const label = sample.method === "Conditional substitution" ? `Conditional · ${sample.condition}` : sample.method === "Headbutt" ? `${sample.method} · ${sample.condition}` : sample.method;
      const detail = sample.rate ? `${sample.rate} encounter rate` : sample.method === "Headbutt" ? "Matching source slots" : "";
      const rows = group.map(e => `<tr><td>${icon(e.icon, "poke-icon")}</td><th scope="row"><strong>${esc(e.name)}</strong>${typeChips(e.types)}</th><td>${e.min ? `Lv. ${esc(e.min)}${e.max !== e.min ? "–" + esc(e.max) : ""}` : "—"}</td><td class="time-badge">${esc(e.time)}</td><td>${esc(e.share || (e.slots ? e.slots + " slots" : "—"))}</td><td class="ability-cell">${esc(e.abilities?.join(" / ") || "Unknown")}${e.hiddenAbility ? `<small>Hidden: ${esc(e.hiddenAbility)}</small>` : ""}${e.abilityNote ? `<small>${esc(e.abilityNote)}</small>` : ""}</td><td class="held-inline">${icon(e.commonSprite, "small-sprite")} ${esc(e.common || "—")}</td><td class="held-inline">${icon(e.rareSprite, "small-sprite")} ${esc(e.rare || "—")}</td></tr>`).join("");
      return `<div class="method-block"><div class="method-heading ${kind}"><h4><span aria-hidden="true">${methodIcon(sample.method)}</span> ${esc(label)}</h4><span class="detail">${esc(detail)}</span></div><div class="table-scroll" tabindex="0" aria-label="${esc(area.name)} ${esc(label)} encounter table, scroll horizontally if needed"><table class="encounter-table"><caption class="sr-only">${esc(area.name)}: ${esc(label)} encounters</caption><thead><tr><th scope="col" aria-label="Sprite"></th><th scope="col">Pokémon</th><th scope="col">Level</th><th scope="col">Time</th><th scope="col">Slot share</th><th scope="col">Possible abilities</th><th scope="col">Common held</th><th scope="col">Rare held</th></tr></thead><tbody>${rows}</tbody></table></div></div>`;
    }).join("");
    return `<article class="area-card" id="wild-area-${DATA.wild.indexOf(area)}"><div class="area-title"><h3 tabindex="-1">${esc(area.name)}</h3><small>${area.table ? "Encounter table " + esc(area.table) : "Headbutt source"}</small></div>${blocks}</article>`;
  }

  function shopCard(shop) {
    const entries = shop.items.map(item => `<div class="shop-item">${icon(item.sprite, "shop-icon")}<div><div class="item-name">${esc(itemLabel(item.name))}</div><small>${price(item.price)}${item.badges ? ` · ${esc(item.badges)} badges required` : ""}</small></div></div>`).join("");
    return `<article class="shop-card"><div class="shop-title"><h3>${esc(shop.name)}</h3><small>${esc(shop.floor)}</small></div><div class="shop-items">${entries}</div></article>`;
  }

  function shopTable(location, counters, rows) {
    const body = rows.map(({ item, floor }) => `<tr><td>${icon(item.sprite, "shop-icon")}</td><th scope="row">${esc(itemLabel(item.name))}</th><td class="shop-price">${price(item.price)}</td><td>${esc(floor || "Standard counter")}</td><td>${item.badges ? `${esc(item.badges)} badges` : "—"}</td></tr>`).join("");
    return `<article class="shop-card"><div class="shop-title"><h3>${esc(location)}</h3><small>${counters.length} ${counters.length === 1 ? "counter" : "counters"}</small></div><div class="table-scroll" tabindex="0" aria-label="${esc(location)} stock table, scroll horizontally if needed"><table class="reference-table shop-table"><caption class="sr-only">${esc(location)} item prices and stock</caption><thead><tr><th scope="col" aria-label="Item sprite"></th><th scope="col">Item</th><th scope="col">Price</th><th scope="col">Floor / counter</th><th scope="col">Requirement</th></tr></thead><tbody>${body}</tbody></table></div></article>`;
  }

  function filteredArea(area) {
    if (!state.query) return area.entries;
    if (matches([area.name])) return area.entries;
    return area.entries.filter(e => matches([e.name, e.method, e.condition, e.common, e.rare, ...(e.abilities || []), e.hiddenAbility]));
  }
  function trainerMatch(t) {
    return matches([t.name, t.location, t.class, t.id, t.bonusNote, t.battleItems,
      ...t.team.flatMap(m => [m.name, m.held, m.ability, m.mega?.name, m.mega?.ability, ...m.moves])]);
  }

  function pageSlice(rows, size = PAGE) {
    const total = Math.max(1, Math.ceil(rows.length / size));
    state.page = Math.min(state.page, total - 1);
    $("pager").innerHTML = rows.length > size ? `<button id="prevPage" ${state.page === 0 ? "disabled" : ""}>Previous</button><span>Page ${state.page + 1} of ${total} · ${rows.length} results</span><button id="nextPage" ${state.page >= total - 1 ? "disabled" : ""}>Next</button>` : "";
    const prev = $("prevPage"), next = $("nextPage");
    if (prev) prev.onclick = () => { state.page--; state.selectedArea = -1; render(); $("main-content").focus(); window.scrollTo(0, 0); };
    if (next) next.onclick = () => { state.page++; state.selectedArea = -1; render(); $("main-content").focus(); window.scrollTo(0, 0); };
    return rows.slice(state.page * size, (state.page + 1) * size);
  }

  function renderWalk() {
    const chapter = DATA.chapters.find(c => c.number === state.chapter);
    const ts = DATA.trainers.filter(t => chapterNum(t.stage) === state.chapter && trainerMatch(t))
      .sort((a, b) => a.order - b.order || gymOrder(a, b));
    const ws = DATA.wild.filter(a => a.chapter === state.chapter && filteredArea(a).length);
    const ss = DATA.shops.filter(s => s.chapter === state.chapter && (matches([s.name, s.floor]) || s.items.some(i => shopItemMatches(i, s.floor))));
    const is = DATA.items.filter(i => i.chapter === state.chapter && matches([i.type, i.location, itemLabel(i.item), i.notes]));
    const st = DATA.statics.filter(i => i.chapter === state.chapter && matches([i.name, i.area, i.parent]));
    let html = `<h1 class="page-title">${esc(chapter?.label || "Story chapter")}</h1><p class="lead">Follow the chapter through its trainer battles and wild areas. Optional bonus battles appear beside their original story location; rematches have their own guide.</p>`;
    html += stats([ts.length, "trainer parties"], [ws.length, "wild areas"], [ss.length, "shops"], [is.length, "audited ground pickups"]);
    if (ts.length) html += `<section class="section" id="battle-section">${title("Trainer battles", ts.length)}${ts.map(trainerCard).join("")}</section>`;
    if (ws.length) html += `<section class="section" id="wild-section">${title("Wild encounters", ws.length)}${ws.map(a => areaCard(a, filteredArea(a))).join("")}</section>`;
    if (ss.length) html += `<section class="section" id="shop-section">${title("Marts and shops", ss.length)}${ss.map(shopCard).join("")}</section>`;
    if (is.length) html += `<section class="section" id="item-section">${title("Ground pickups", is.length)}${notice("Release v22 event placements and hidden-item parameters. Two visible objects have unresolved item identities; reachability has not been checked.", true)}${itemTable(is)}</section>`;
    if (st.length) html += `<section class="section" id="static-section">${title("Scripted encounters", st.length)}${notice("Species and levels come from script commands; reachability and unlock conditions are not verified.", true)}${staticTable(st)}</section>`;
    if (!ts.length && !ws.length && !ss.length && !is.length && !st.length) html += '<div class="empty">No entries match this search in this chapter.</div>';
    $("pager").innerHTML = "";
    return html;
  }

  function itemTable(rows) {
    return `<div class="table-scroll" tabindex="0" aria-label="Item locations table, scroll horizontally if needed"><table class="reference-table"><caption class="sr-only">Item locations</caption><thead><tr><th scope="col" aria-label="Sprite"></th><th scope="col">Item</th><th scope="col">Where</th><th scope="col">Type</th><th scope="col">Coordinates</th><th scope="col">Notes</th></tr></thead><tbody>${rows.map(i => `<tr><td>${icon(i.sprite)}</td><th scope="row">${esc(itemLabel(i.item))}</th><td>${esc(i.location)}</td><td>${esc(i.type)}</td><td>${esc(i.coord)}</td><td>${esc(i.notes)}</td></tr>`).join("")}</tbody></table></div>`;
  }
  function staticTable(rows) {
    return `<div class="table-scroll" tabindex="0" aria-label="Scripted encounters table, scroll horizontally if needed"><table class="reference-table"><caption class="sr-only">Scripted Pokémon encounters and parent areas</caption><thead><tr><th scope="col" aria-label="Sprite"></th><th scope="col">Pokémon</th><th scope="col">Level</th><th scope="col">Encounter area</th><th scope="col">Parent area</th></tr></thead><tbody>${rows.map(i => `<tr><td>${icon(i.icon, "poke-icon")}</td><th scope="row">${esc(i.name)}</th><td>Lv. ${esc(i.level)}</td><td>${esc(i.area)}</td><td><strong>${esc(i.parent)}</strong><br><small class="dim">${esc(i.parentLink)}</small></td></tr>`).join("")}</tbody></table></div>`;
  }

  function renderTrainers() {
    const groupOrder = Object.fromEntries(DATA.trainerGroups.map((g, index) => [g.id, index]));
    const rows = DATA.trainers.filter(t => (state.trainerGroup === "All" || t.group === state.trainerGroup) && trainerMatch(t));
    rows.sort((a, b) => groupOrder[a.group] - groupOrder[b.group]
      || gymOrder(a, b)
      || a.order - b.order || Number(a.bonus) - Number(b.bonus) || a.id - b.id);
    const shown = pageSlice(rows, 10);
    return `<h1 class="page-title">${state.trainerGroup === "All" ? "Story and bonus trainers" : esc(DATA.trainerGroups.find(g => g.id === state.trainerGroup)?.label || "Trainers")}</h1><p class="lead">Trainer battles in approximate story order, including optional bonus battles. Mega-capable teams show their in-battle Mega sprite, ability, and typing. Each Gym lists its trainers in audited order, then the Leader, then the Leader's Bonus Battle. Elite Four and Champion battles have their own chapters. Rematches are in the separate rematch guide.</p>${stats([rows.length, "matching trainer parties"], [rows.filter(t => t.bonus).length, "bonus parties included"])}${shown.map(trainerCard).join("") || '<div class="empty">No trainers match.</div>'}`;
  }

  function renderWild() {
    const rows = DATA.wild.filter(a => filteredArea(a).length);
    const shown = pageSlice(rows, WILD_PAGE);
    return `<h1 class="page-title">Wild encounter atlas</h1><p class="lead">Browse Pokémon by area and method, or jump to a location from the sidebar. Slot share is the chance after an encounter is triggered. Abilities list the possible normal abilities and the hidden ability from the species data; an individual wild Pokémon's ability is not fixed by this table.</p>${stats([rows.length, "matching areas"], [DATA.wild.length, "areas total"])}${shown.map(a => areaCard(a, filteredArea(a))).join("") || '<div class="empty">No wild areas match.</div>'}`;
  }
  function renderShops() {
    const selected = shopTabs.find(tab => tab.key === state.shopLocation);
    const location = selected?.label || "";
    const counters = selected?.counters || [];
    const locationMatches = matches([location]);
    const rows = counters.flatMap(shop => shop.items.map(item => ({ item, floor: shop.floor })))
      .filter(({ item, floor }) => locationMatches || shopItemMatches(item, floor));
    $("pager").innerHTML = "";
    return `<h1 class="page-title">${esc(location || "Marts and department stores")}</h1><p class="lead">Select a shop, floor, or counter in the sidebar to see its stock and prices. Search by TM number or move name to find a TM. Standard mart stock grows with badge count.</p>${stats([shopTabs.length, "shop tabs"], [counters.length, counters.length === 1 ? "counter" : "counters"], [rows.length, "listed items"])}${rows.length ? shopTable(location, counters, rows) : '<div class="empty">No items match this search at this location.</div>'}`;
  }

  const statNames = ["HP", "Attack", "Defense", "Sp. Atk", "Sp. Def", "Speed"];
  const dexStatColumns = [["HP", "hp"], ["Atk", "attack", "Attack"], ["Def", "defense", "Defense"],
    ["Sp. Atk", "spAttack", "Special Attack"], ["Sp. Def", "spDefense", "Special Defense"], ["Speed", "speed"]];
  const dexNameOrder = new Intl.Collator("en", { sensitivity: "base", numeric: true });
  const statTotal = mon => mon.stats.reduce((sum, value) => sum + value, 0);

  function learnsetSection(label, columns, rows, open = false) {
    const table = `<div class="table-scroll"><table class="reference-table dex-table"><caption class="sr-only">${label} moves</caption><thead><tr>${columns.map(name => `<th scope="col">${name}</th>`).join("")}</tr></thead><tbody>${rows.map(row => `<tr>${row.map(cell => `<td>${esc(cell)}</td>`).join("")}</tr>`).join("")}</tbody></table></div>`;
    return `<details class="dex-learnset"${open ? " open" : ""}><summary>${label} <span class="dim">(${rows.length})</span></summary>${rows.length ? table : '<p class="dex-empty">None listed for this Pokémon.</p>'}</details>`;
  }

  function pokemonDetails(mon) {
    const yields = mon.evs.flatMap((value, index) => value ? [`${value} ${statNames[index]}`] : []);
    const facts = [
      ["Catch rate", mon.catchRate], ["Base friendship", mon.friendship], ["Growth rate", mon.growth],
      ["Egg groups", mon.eggGroups.join(" / ")], ["EV yield", yields.join(", ") || "None"],
    ];
    const abilities = mon.abilities.map(ability => `<li>${esc(ability)}</li>`);
    if (mon.hidden) abilities.push(`<li>${esc(mon.hidden)} <small>Hidden ability</small></li>`);
    // This release uses TM001–TM092 and HMs. Retain later TMs and TRs in the engine data.
    const machines = mon.machines.filter(code => {
      if (code.startsWith("HM")) return true;
      if (!code.startsWith("TM")) return false;
      const number = Number(code.slice(2));
      return number >= 1 && number <= 92;
    });
    return `<button type="button" class="dex-back" id="dexBack">← Back to Pokémon list</button>
      <header class="dex-profile">
        <div class="dex-stage" aria-hidden="true">${imageName(mon)}</div>
        <div class="dex-profile-copy">
          <div class="dex-kicker">${mon.form ? "Alternate form" : "Pokédex entry"}</div>
          <h1 class="page-title" id="dexTitle" tabindex="-1">${esc(mon.name)}</h1>
          ${mon.category ? `<p class="dex-category">${esc(mon.category)}</p>` : ""}
          ${typeChips(mon.types)}
          ${mon.description ? `<p class="dex-description">${esc(mon.description)}</p>` : ""}
          ${mon.height || mon.weight ? `<dl class="dex-measurements">${[["Height", mon.height], ["Weight", mon.weight]].filter(([, value]) => value).map(([name, value]) => `<div><dt>${name}</dt><dd>${esc(value)}</dd></div>`).join("")}</dl>` : ""}
        </div>
      </header>
      <div class="dex-overview">
        <section class="dex-panel"><div class="dex-panel-title"><h2>Base stats</h2><span class="dex-total"><strong>${statTotal(mon)}</strong> total</span></div>
          <dl class="dex-stats">${mon.stats.map((value, index) => `<div><dt>${statNames[index]}</dt><dd><span>${value}</span><span class="dex-meter" aria-hidden="true" style="--fill:${value / 255 * 100}%"></span></dd></div>`).join("")}</dl>
        </section>
        <section class="dex-panel"><h2>Abilities and species data</h2>
          ${abilities.length ? `<ul class="dex-abilities" aria-label="Abilities">${abilities.join("")}</ul>` : "<p>No abilities listed.</p>"}
          <dl class="dex-facts">${facts.filter(([, value]) => value !== "").map(([name, value]) => `<div><dt>${name}</dt><dd>${esc(value)}</dd></div>`).join("")}</dl>
        </section>
      </div>
      <section class="section dex-moves">${title("Learnset")}
        ${learnsetSection("Level up", ["Level", "Move"], mon.level.map(([level, move]) => [level === 0 ? "On evolution" : level, move]), true)}
        ${learnsetSection("TMs and HMs", ["Machine", "Move"], machines.map(code => [code, machineMoves[code]]))}
        ${learnsetSection("Egg moves", ["Move"], mon.egg.map(move => [move]))}
        ${learnsetSection("Tutor moves", ["Move"], mon.tutor.map(move => [move]))}
      </section>`;
  }

  function sortDexRows(rows) {
    const { column, direction } = dexSort;
    const statIndex = dexStatColumns.findIndex(([, key]) => key === column);
    let compare;
    if (column === "number") compare = (a, b) => a.dexNumber - b.dexNumber;
    else if (column === "name") compare = (a, b) => dexNameOrder.compare(a.name, b.name);
    else if (column === "bst") compare = (a, b) => statTotal(a) - statTotal(b);
    else compare = (a, b) => a.stats[statIndex] - b.stats[statIndex];
    rows.sort((a, b) => direction * compare(a, b) || a.dexNumber - b.dexNumber || Number(a.form) - Number(b.form));
  }

  function dexTable(rows) {
    const columns = [["Icon"], ["#", "number", "Pokédex number"], ["Name", "name"], ["Type"],
      ["Ability 1"], ["Ability 2"], ["Ability 3"], ...dexStatColumns, ["BST", "bst", "Base stat total"]];
    const headings = columns.map(([label, key, fullLabel]) => {
      if (!key) return `<th scope="col">${label}</th>`;
      const active = key === dexSort.column;
      const ascending = dexSort.direction === 1;
      const arrow = active ? (ascending ? "↑" : "↓") : "↕";
      return `<th scope="col"${key === "name" ? "" : ' class="dex-number"'}${active ? ` aria-sort="${ascending ? "ascending" : "descending"}"` : ""}><button type="button" data-dex-sort="${key}"${fullLabel ? ` aria-label="${fullLabel}" title="${fullLabel}"` : ""}>${label} <span aria-hidden="true">${arrow}</span></button></th>`;
    }).join("");
    const body = rows.map(mon => `<tr>
      <td class="dex-icon-cell">${mon.icon ? icon(mon.icon, "poke-icon", "", true) : imageName(mon)}</td>
      <td class="dex-number">${String(mon.dexNumber).padStart(3, "0")}</td>
      <th scope="row"><button type="button" id="dex-${mon.token}" data-pokemon="${mon.token}">${esc(mon.name)}</button></th>
      <td>${typeChips(mon.types)}</td>
      ${[...mon.abilitySlots, mon.hidden].map(ability => `<td>${esc(ability || "—")}</td>`).join("")}
      ${mon.stats.map(stat => `<td class="dex-number">${stat}</td>`).join("")}
      <td class="dex-number dex-bst">${statTotal(mon)}</td>
    </tr>`).join("");
    return `<div class="dex-table-frame"><div class="table-scroll dex-list" tabindex="0" aria-label="Pokédex table, scroll horizontally if needed"><table class="reference-table dex-index-table"><caption class="sr-only">National Pokédex species and forms. Ability 3 is the hidden ability.</caption><thead><tr>${headings}</tr></thead><tbody>${body}</tbody></table></div></div>`;
  }

  function renderPokedex() {
    $("pager").innerHTML = "";
    if (selectedPokemon) return pokemonDetails(selectedPokemon);
    const numberSearch = /^#?\d+$/.test(state.query) ? Number(state.query.replace("#", "")) : null;
    const rows = pokedex.filter(mon => mon.dexNumber && (numberSearch !== null ? mon.dexNumber === numberSearch
      : matches([mon.name, ...mon.types, ...mon.abilities, mon.hidden])));
    sortDexRows(rows);
    return `<header class="dex-index">
      <div><h1 class="page-title">Pokédex</h1><p>Select a column heading to sort. Ability 3 is the hidden ability.</p></div>
      ${stats([rows.length.toLocaleString(), state.query ? "matching entries" : "species and forms"])}</header>
      ${rows.length ? dexTable(rows) : '<div class="empty">No Pokémon match this search.</div>'}`;
  }

  function bindPokedex() {
    if (selectedPokemon) {
      $("dexBack").onclick = () => {
        const token = selectedPokemon.token;
        selectedPokemon = null;
        render();
        const list = $("content").querySelector(".dex-list");
        list.scrollLeft = dexListScroll.left;
        window.scrollTo(0, dexListScroll.page);
        $(`dex-${token}`)?.focus({ preventScroll: true });
      };
    } else {
      const list = $("content").querySelector(".dex-list");
      if (!list) return;
      list.onclick = event => {
        const heading = event.target.closest("[data-dex-sort]");
        if (heading) {
          const column = heading.dataset.dexSort;
          const left = list.scrollLeft;
          dexSort.direction = column === dexSort.column ? -dexSort.direction : (column === "number" || column === "name" ? 1 : -1);
          dexSort.column = column;
          render();
          const updatedList = $("content").querySelector(".dex-list");
          updatedList.scrollLeft = left;
          if (updatedList.getBoundingClientRect().top < 0) updatedList.scrollIntoView({ block: "start", inline: "nearest" });
          updatedList.querySelector(`[data-dex-sort="${column}"]`).focus({ preventScroll: true });
          return;
        }
        const button = event.target.closest("[data-pokemon]");
        if (!button) return;
        dexListScroll = { left: list.scrollLeft, page: window.scrollY };
        selectedPokemon = pokedex.find(mon => mon.token === button.dataset.pokemon);
        render();
        $("dexTitle").focus({ preventScroll: true });
        $("dexBack").scrollIntoView({ block: "start" });
      };
    }
  }

  function renderItems() {
    const rows = DATA.items.filter(i => matches([i.type, i.location, itemLabel(i.item), i.coord, i.notes]));
    const shown = pageSlice(rows, 60);
    return `<h1 class="page-title">Ground item locations</h1><p class="lead">Visible item balls and hidden pickups from the Release v22 event files. Coordinates are map coordinates. Script gifts and older guide claims are listed in the linked audit files below.</p>${notice("Two visible item objects have unresolved identities in this extraction. A listed placement does not confirm that it is reachable during play.", true)}<p><a href="Release-v22-Item-Audit.md">Read audit notes</a> · <a href="Release-v22-Script-Item-Interactions.csv">Script item interactions</a> · <a href="Item-Locations.csv">Historical item list</a></p>${stats([rows.length, "matching pickups"])}${shown.length ? itemTable(shown) : '<div class="empty">No items match.</div>'}`;
  }
  function renderEvolution() {
    const rows = DATA.evos.filter(e => matches([e.from, e.to, e.requirement, e.method]));
    const shown = pageSlice(rows, 70);
    const table = `<div class="table-scroll" tabindex="0" aria-label="Evolution guide table, scroll horizontally if needed"><table class="reference-table"><caption class="sr-only">Pokémon evolution requirements</caption><thead><tr><th scope="col">From</th><th scope="col">Evolves into</th><th scope="col">Requirement</th><th scope="col">Engine method</th></tr></thead><tbody>${shown.map(e => `<tr><th scope="row">${icon(e.fromIcon, "poke-icon")} ${esc(e.from)}</th><td>${icon(e.toIcon, "poke-icon")} <strong>${esc(e.to)}</strong></td><td>${esc(e.requirement)}</td><td class="dim">${esc(e.method)}</td></tr>`).join("")}</tbody></table></div>`;
    return `<h1 class="page-title">Evolution guide</h1><p class="lead">Search either Pokémon or an item. Special engine methods may still need in-game verification.</p>${stats([rows.length, "matching methods"])}${shown.length ? table : '<div class="empty">No evolutions match.</div>'}`;
  }
  function renderStatic() {
    const rows = DATA.statics.filter(i => matches([i.name, i.area, i.parent, i.level]));
    const shown = pageSlice(rows, 70);
    return `<h1 class="page-title">Scripted Pokémon encounters</h1>${notice("Script data identifies species and levels, but does not establish reachability or unlock conditions.", true)}${stats([rows.length, "matching encounters"])}${shown.length ? staticTable(shown) : '<div class="empty">No scripted encounters match.</div>'}`;
  }
  function renderRematches() {
    const rows = DATA.trainers.filter(t => (state.filter === "All" || t.rematchInfo.kind === state.filter) && trainerMatch(t));
    rows.sort((a, b) => chapterNum(a.stage) - chapterNum(b.stage) || Number(a.rematchInfo.base) - Number(b.rematchInfo.base) || a.id - b.id);
    const shown = pageSlice(rows, 10);
    return `<h1 class="page-title">${state.filter === "All" ? "Rematch trainers" : esc(state.filter + " rematches")}</h1><p class="lead">Rematch parties are shown separately from story and bonus battles. Their order follows the original trainer’s story location; rematch availability can depend on later progress or schedules.</p>${stats([rows.length, "matching rematch parties"], [DATA.counts.rematches, "total rematches"])}${shown.map(trainerCard).join("") || '<div class="empty">No rematches match.</div>'}`;
  }

  function renderLocationList() {
    const nav = $("locationNav"), list = nav.querySelector(".location-list");
    const filtered = DATA.wild.map((area, index) => ({ area, index }))
      .filter(({ area }) => area.name.toLocaleLowerCase().includes(state.locationQuery));
    nav.querySelector(".location-count").textContent = `${filtered.length} of ${DATA.wild.length} locations`;
    list.innerHTML = filtered.length ? filtered.map(({ area, index }) =>
      `<button type="button" data-area-index="${index}" class="${state.selectedArea === index ? "active" : ""}" aria-current="${state.selectedArea === index ? "location" : "false"}">${esc(area.name)}</button>`
    ).join("") : '<p class="location-empty">No locations match.</p>';
    list.querySelectorAll("button").forEach(button => button.onclick = () => {
      const index = Number(button.dataset.areaIndex);
      state.query = "";
      state.page = Math.floor(index / WILD_PAGE);
      state.selectedArea = index;
      $("search").value = "";
      render();
      const heading = document.querySelector(`#wild-area-${index} .area-title h3`);
      heading?.scrollIntoView({ block: "start" });
      heading?.focus({ preventScroll: true });
    });
  }

  function renderLocationNav() {
    const nav = $("locationNav");
    nav.hidden = REMATCH || state.view !== "wild";
    if (nav.hidden) return;
    const previousScroll = nav.querySelector(".location-list")?.scrollTop || 0;
    nav.innerHTML = `<h3>Jump to location</h3><label for="locationSearch">Find a location</label><input id="locationSearch" type="search" placeholder="Route, town, cave…" value="${esc(state.locationQuery)}"><div class="location-count" aria-live="polite"></div><div class="location-list" tabindex="0" aria-label="Wild encounter locations"></div>`;
    nav.querySelector("#locationSearch").oninput = event => {
      state.locationQuery = event.target.value.trim().toLocaleLowerCase();
      renderLocationList();
    };
    renderLocationList();
    nav.querySelector(".location-list").scrollTop = previousScroll;
  }

  function renderNav() {
    const views = REMATCH ? [["rematches", "Rematch trainers"]] : [["walk", "Story walkthrough"], ...(pokedex.length ? [["pokedex", "Pokédex"]] : []), ["trainers", "Trainers"], ["wild", "Wild atlas"], ["shops", "Marts & stores"], ["items", "Item locations"], ["evolution", "Evolutions"], ["static", "Static encounters"]];
    $("viewNav").innerHTML = views.map(([key, label]) => `<button type="button" data-view="${key}" class="${state.view === key ? "active" : ""}" aria-current="${state.view === key ? "page" : "false"}">${esc(label)}</button>`).join("");
    $("viewNav").querySelectorAll("button").forEach(button => button.onclick = () => { state.view = button.dataset.view; state.page = 0; state.query = ""; state.selectedArea = -1; selectedPokemon = null; $("search").value = ""; render(); $("main-content").focus(); });
    if (state.view === "walk") {
      $("chapterNav").innerHTML = `<h3>Story chapters</h3>${DATA.chapters.map(c => `<button type="button" data-chapter="${c.number}" class="${state.chapter === c.number ? "active" : ""}" aria-current="${state.chapter === c.number ? "page" : "false"}">${esc(c.label)}</button>`).join("")}`;
      $("chapterNav").querySelectorAll("button").forEach(button => button.onclick = () => { state.chapter = Number(button.dataset.chapter); state.page = 0; render(); $("main-content").focus(); window.scrollTo(0, 0); });
    } else if (state.view === "trainers") {
      $("chapterNav").innerHTML = `<h3>Trainer chapters</h3><button type="button" data-trainer-group="All" class="${state.trainerGroup === "All" ? "active" : ""}" aria-pressed="${state.trainerGroup === "All"}">All trainers</button>${DATA.trainerGroups.map(g => `<button type="button" data-trainer-group="${esc(g.id)}" class="${state.trainerGroup === g.id ? "active" : ""}" aria-pressed="${state.trainerGroup === g.id}">${esc(g.label)}</button>`).join("")}`;
      $("chapterNav").querySelectorAll("button").forEach(button => button.onclick = () => { state.trainerGroup = button.dataset.trainerGroup; state.page = 0; render(); $("main-content").focus(); window.scrollTo(0, 0); });
    } else if (state.view === "shops") {
      const matchingTabs = shopTabs.filter(tab => matches([tab.label]) || tab.counters.some(shop => shop.items.some(item => shopItemMatches(item, shop.floor))));
      if (!matchingTabs.some(tab => tab.key === state.shopLocation)) state.shopLocation = matchingTabs[0]?.key || shopTabs[0]?.key || "";
      $("chapterNav").innerHTML = `<h3>Mart locations, floors and counters</h3>${shopTabs.map((tab, index) => `<button type="button" data-shop-index="${index}" class="${state.shopLocation === tab.key ? "active" : ""}" aria-current="${state.shopLocation === tab.key ? "page" : "false"}">${esc(tab.label)}</button>`).join("")}`;
      $("chapterNav").querySelectorAll("button").forEach(button => button.onclick = () => { state.shopLocation = shopTabs[Number(button.dataset.shopIndex)].key; state.query = ""; $("search").value = ""; render(); $("main-content").focus(); window.scrollTo(0, 0); });
    } else if (state.view === "rematches") {
      const kinds = ["All", "Phone rematch", "Gym Leader", "Pokémon League"];
      $("chapterNav").innerHTML = `<h3>Rematch groups</h3>${kinds.map(kind => `<button type="button" data-filter="${esc(kind)}" class="${state.filter === kind ? "active" : ""}" aria-pressed="${state.filter === kind}">${esc(kind)}</button>`).join("")}`;
      $("chapterNav").querySelectorAll("button").forEach(button => button.onclick = () => { state.filter = button.dataset.filter; state.page = 0; render(); $("main-content").focus(); });
    } else $("chapterNav").innerHTML = "";
    renderLocationNav();
  }
  function render() {
    renderNav();
    $("breadcrumb").textContent = REMATCH ? "Reference / Rematch trainers" : state.view === "walk" ? `Walkthrough / Chapter ${String(state.chapter).padStart(2, "0")}` : `Reference / ${state.view}`;
    $("content").innerHTML = ({ walk: renderWalk, pokedex: renderPokedex, trainers: renderTrainers, wild: renderWild, shops: renderShops, items: renderItems, evolution: renderEvolution, static: renderStatic, rematches: renderRematches })[state.view]();
    if (state.view === "pokedex") bindPokedex();
    $("search").placeholder = state.view === "pokedex" ? "Names, Pokédex numbers, types or abilities" : "Names, areas, items, moves or abilities";
    $("resultsStatus").textContent = $("content").querySelector(".stats")?.textContent.trim().replace(/\s+/g, " ") || "Guide content updated";
  }
  $("search").addEventListener("input", event => { state.query = event.target.value.trim().toLocaleLowerCase(); state.page = 0; state.selectedArea = -1; selectedPokemon = null; render(); });
  $("printBtn").onclick = () => window.print();
  $("textSizeBtn").onclick = () => {
    const larger = document.documentElement.classList.toggle("large-text");
    $("textSizeBtn").setAttribute("aria-pressed", String(larger));
    $("textSizeBtn").textContent = larger ? "Standard text" : "Larger text";
    try { localStorage.setItem("heartfelt-guide-large-text", larger ? "1" : "0"); } catch (_) {}
  };
  try {
    if (localStorage.getItem("heartfelt-guide-large-text") === "1") {
      document.documentElement.classList.add("large-text");
      $("textSizeBtn").setAttribute("aria-pressed", "true");
      $("textSizeBtn").textContent = "Standard text";
    }
  } catch (_) {}
  render();
})();
