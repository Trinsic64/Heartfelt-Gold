(() => {
  "use strict";
  const DATA = window.GUIDE_DATA;
  const REMATCH = DATA.mode === "rematch";
  const state = { view: REMATCH ? "rematches" : "walk", chapter: 1, trainerGroup: "All", filter: "All", page: 0, query: "", locationQuery: "", selectedArea: -1 };
  const PAGE = 8;
  const WILD_PAGE = 6;
  const $ = id => document.getElementById(id);
  const esc = value => String(value ?? "").replace(/[&<>"']/g, ch => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[ch]));
  const icon = (src, cls = "small-sprite", alt = "") => src ? `<img class="${cls}" src="${esc(src.startsWith("Sprites/Items/") ? src + "?v=2" : src)}" alt="${esc(alt)}">` : "";
  const chapterNum = value => Number.parseInt(String(value).slice(0, 2), 10) || 45;
  // Keep audited Gym Trainer order, then the Leader, then the Bonus Battle.
  const gymRank = trainer => trainer.bonus ? 2 : trainer.major ? 1 : 0;
  const gymOrder = (a, b) => a.group === b.group && a.group?.startsWith("gym-") ? gymRank(a) - gymRank(b) : 0;
  const matches = (values, q = state.query) => !q || values.some(v => String(v ?? "").toLocaleLowerCase().includes(q));
  const title = (text, count = "") => `<h2>${esc(text)}${count === "" ? "" : `<small>${count} ${count === 1 ? "entry" : "entries"}</small>`}</h2>`;
  const notice = (text, blue = false) => `<div class="notice${blue ? " blue" : ""}">${esc(text)}</div>`;
  const stats = (...values) => `<div class="stats">${values.map(([n, label]) => `<span class="stat"><strong>${esc(n)}</strong> ${esc(label)}</span>`).join("")}</div>`;
  const chip = text => `<span class="badge">${esc(text)}</span>`;
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
    const team = t.team.map(m => `<div class="mon-card">
      <div class="mon-top">${imageName(m)}<div><div class="mon-name">${esc(m.name)}</div><div class="level">Lv. ${esc(m.level)}</div></div></div>
      ${typeChips(m.types)}<div class="ability"><strong>Ability:</strong> ${esc(m.ability)}${m.abilitySlot === "Hidden" ? ' <span class="ability-kind">(Hidden)</span>' : ""}</div><div class="held"><strong>Held:</strong> ${icon(m.heldSprite, "small-sprite")}<span>${esc(m.held || "No held item")}</span></div>
      <div class="moves">${m.moves.length ? m.moves.map(move => `<span class="move">${esc(move)}</span>`).join("") : `<span class="move dim">Moves not listed</span>`}</div>
    </div>`).join("");
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
    const entries = shop.items.map(item => `<div class="shop-item">${icon(item.sprite, "small-sprite", item.name)}<div><div class="item-name">${esc(item.name)}</div>${item.badges ? `<small>${esc(item.badges)} badges required</small>` : ""}</div></div>`).join("");
    return `<article class="shop-card"><div class="shop-title"><h3>${esc(shop.name)}</h3><small>${esc(shop.floor)}</small></div><div class="shop-items">${entries}</div></article>`;
  }

  function filteredArea(area) {
    if (!state.query) return area.entries;
    if (matches([area.name])) return area.entries;
    return area.entries.filter(e => matches([e.name, e.method, e.condition, e.common, e.rare, ...(e.abilities || []), e.hiddenAbility]));
  }
  function trainerMatch(t) {
    return matches([t.name, t.location, t.class, t.id, t.bonusNote, t.battleItems,
      ...t.team.flatMap(m => [m.name, m.held, m.ability, ...m.moves])]);
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
    const ss = DATA.shops.filter(s => s.chapter === state.chapter && matches([s.name, s.floor, ...s.items.map(i => i.name)]));
    const is = DATA.items.filter(i => i.chapter === state.chapter && matches([i.type, i.location, i.item, i.notes]));
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
    return `<div class="table-scroll" tabindex="0" aria-label="Item locations table, scroll horizontally if needed"><table class="reference-table"><caption class="sr-only">Item locations</caption><thead><tr><th scope="col" aria-label="Sprite"></th><th scope="col">Item</th><th scope="col">Where</th><th scope="col">Type</th><th scope="col">Coordinates</th><th scope="col">Notes</th></tr></thead><tbody>${rows.map(i => `<tr><td>${icon(i.sprite)}</td><th scope="row">${esc(i.item)}</th><td>${esc(i.location)}</td><td>${esc(i.type)}</td><td>${esc(i.coord)}</td><td>${esc(i.notes)}</td></tr>`).join("")}</tbody></table></div>`;
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
    return `<h1 class="page-title">${state.trainerGroup === "All" ? "Story and bonus trainers" : esc(DATA.trainerGroups.find(g => g.id === state.trainerGroup)?.label || "Trainers")}</h1><p class="lead">Trainer battles in approximate story order, including optional bonus battles. Each Gym lists its trainers in audited order, then the Leader, then the Leader's Bonus Battle. Elite Four and Champion battles have their own chapters. Rematches are in the separate rematch guide.</p>${stats([rows.length, "matching trainer parties"], [rows.filter(t => t.bonus).length, "bonus parties included"])}${shown.map(trainerCard).join("") || '<div class="empty">No trainers match.</div>'}`;
  }

  function renderWild() {
    const rows = DATA.wild.filter(a => filteredArea(a).length);
    const shown = pageSlice(rows, WILD_PAGE);
    return `<h1 class="page-title">Wild encounter atlas</h1><p class="lead">Browse Pokémon by area and method, or jump to a location from the sidebar. Slot share is the chance after an encounter is triggered. Abilities list the possible normal abilities and the hidden ability from the species data; an individual wild Pokémon's ability is not fixed by this table.</p>${stats([rows.length, "matching areas"], [DATA.wild.length, "areas total"])}${shown.map(a => areaCard(a, filteredArea(a))).join("") || '<div class="empty">No wild areas match.</div>'}`;
  }
  function renderShops() {
    const rows = DATA.shops.filter(s => matches([s.name, s.floor, ...s.items.map(i => i.name)]));
    const shown = pageSlice(rows, 8);
    return `<h1 class="page-title">Marts and department stores</h1><p class="lead">Configured stock from the local engine source. Standard mart stock grows with badge count; listed prices were not supplied by these stock arrays.</p>${stats([rows.length, "shop counters"])}${shown.map(shopCard).join("") || '<div class="empty">No shops match.</div>'}`;
  }
  function renderItems() {
    const rows = DATA.items.filter(i => matches([i.type, i.location, i.item, i.coord, i.notes]));
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
    const views = REMATCH ? [["rematches", "Rematch trainers"]] : [["walk", "Story walkthrough"], ["trainers", "Trainers"], ["wild", "Wild atlas"], ["shops", "Marts & stores"], ["items", "Item locations"], ["evolution", "Evolutions"], ["static", "Static encounters"]];
    $("viewNav").innerHTML = views.map(([key, label]) => `<button type="button" data-view="${key}" class="${state.view === key ? "active" : ""}" aria-current="${state.view === key ? "page" : "false"}">${esc(label)}</button>`).join("");
    $("viewNav").querySelectorAll("button").forEach(button => button.onclick = () => { state.view = button.dataset.view; state.page = 0; state.query = ""; state.selectedArea = -1; $("search").value = ""; render(); $("main-content").focus(); });
    if (state.view === "walk") {
      $("chapterNav").innerHTML = `<h3>Story chapters</h3>${DATA.chapters.map(c => `<button type="button" data-chapter="${c.number}" class="${state.chapter === c.number ? "active" : ""}" aria-current="${state.chapter === c.number ? "page" : "false"}">${esc(c.label)}</button>`).join("")}`;
      $("chapterNav").querySelectorAll("button").forEach(button => button.onclick = () => { state.chapter = Number(button.dataset.chapter); state.page = 0; render(); $("main-content").focus(); window.scrollTo(0, 0); });
    } else if (state.view === "trainers") {
      $("chapterNav").innerHTML = `<h3>Trainer chapters</h3><button type="button" data-trainer-group="All" class="${state.trainerGroup === "All" ? "active" : ""}" aria-pressed="${state.trainerGroup === "All"}">All trainers</button>${DATA.trainerGroups.map(g => `<button type="button" data-trainer-group="${esc(g.id)}" class="${state.trainerGroup === g.id ? "active" : ""}" aria-pressed="${state.trainerGroup === g.id}">${esc(g.label)}</button>`).join("")}`;
      $("chapterNav").querySelectorAll("button").forEach(button => button.onclick = () => { state.trainerGroup = button.dataset.trainerGroup; state.page = 0; render(); $("main-content").focus(); window.scrollTo(0, 0); });
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
    $("content").innerHTML = ({ walk: renderWalk, trainers: renderTrainers, wild: renderWild, shops: renderShops, items: renderItems, evolution: renderEvolution, static: renderStatic, rematches: renderRematches })[state.view]();
    $("resultsStatus").textContent = $("content").querySelector(".stats")?.textContent.trim().replace(/\s+/g, " ") || "Guide content updated";
  }
  $("search").addEventListener("input", event => { state.query = event.target.value.trim().toLocaleLowerCase(); state.page = 0; state.selectedArea = -1; render(); });
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
