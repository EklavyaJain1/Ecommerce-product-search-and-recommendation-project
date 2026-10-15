/* ShopMind storefront — talks to the Flask search engine. */
"use strict";

const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => Array.from(document.querySelectorAll(sel));

const money = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" });
const countFmt = new Intl.NumberFormat("en-US");

const COLOR_HEX = {
  black: "#17191C", ivory: "#F1EDE4", slate: "#5C6A78", sand: "#D9C7A7",
  olive: "#6B7350", charcoal: "#33363B", burgundy: "#6E2A31", sky: "#A9C6DE",
  forest: "#2F4F3A", blush: "#E4C3C0", graphite: "#4A4E55", cream: "#EFE6D5",
};

const state = {
  q: "",
  cats: new Set(),
  minPrice: null,
  maxPrice: null,
  minRating: 0,
  inStock: false,
  sort: "trending",
  page: 1,
  perPage: 24,
  total: 0,
  items: [],
  facets: null,
  cart: [],
  viewed: [],
  suppressHistory: false,
};

/* --------------------------------------------------------------- derivations
   Presentation only — sale badges, badges and swatches are derived from the
   catalogue's own numbers so no extra server fields are needed. */
const onSale = (p) => (p.id * 7919) % 10 < 3;
const compareAt = (p) => (Math.ceil(p.price * 1.3) - 0.01);
const discountPct = (p) => Math.round((1 - p.price / compareAt(p)) * 100);
const isNew = (p) => p.age_days <= 90;
const isBest = (p) => p.rating_count >= 5000 && p.rating >= 4.6;
const freeShip = (p) => p.price >= 75;

function swatches(p) {
  const found = [];
  for (const tag of p.tags || []) {
    const key = String(tag).toLowerCase();
    if (COLOR_HEX[key] && !found.includes(key)) found.push(key);
  }
  return found.slice(0, 5);
}

function starsHTML(rating) {
  const pct = Math.max(0, Math.min(100, (rating / 5) * 100));
  return `<span class="stars" style="--fill:${pct}%" aria-hidden="true"><span></span></span>`;
}

function moneyHTML(p) {
  const was = onSale(p) ? `<s class="price-was">${money.format(compareAt(p))}</s>` : "";
  return `<p class="price"><span class="price-now">${money.format(p.price)}</span>${was}</p>`;
}

function badgesHTML(p) {
  const out = [];
  if (p.stock <= 0) out.push('<li class="badge badge-out">Sold Out</li>');
  else {
    if (onSale(p)) out.push(`<li class="badge badge-sale">Save ${discountPct(p)}%</li>`);
    else if (isNew(p)) out.push('<li class="badge badge-new">New</li>');
    if (isBest(p)) out.push('<li class="badge badge-best">Best Seller</li>');
  }
  return out.length ? `<ul class="badges">${out.join("")}</ul>` : "";
}

/* One photo per product type where the catalogue has an openly-licensed image
   for it; otherwise the built-in duotone illustration stands in. Cards keep the
   image decorative because the product name sits directly beneath it. */
function productImage(p, alt = "") {
  if (!p.image) return "";
  return `<img class="product-img" src="/static/${esc(p.image)}" alt="${esc(alt)}" loading="lazy" decoding="async">`;
}

function cardHTML(p, index) {
  const dept = deptStyle(p.category);
  const icon = iconKeyFor(p);
  const soldOut = p.stock <= 0;
  const low = !soldOut && p.stock <= 12;
  const sw = swatches(p);
  return `
  <article class="card">
    <div class="thumb" style="--tint:${dept.tint};--tint-ink:${dept.ink}">
      ${p.image ? productImage(p) : iconSvg(icon, "thumb-icon")}
      ${badgesHTML(p)}
      <button class="quick-add" type="button" data-add="${p.id}" ${soldOut ? "disabled" : ""}>
        ${soldOut ? "Sold Out" : "Add to Cart"}
      </button>
    </div>
    <div class="card-body">
      <p class="card-brand">${esc(p.brand)}</p>
      <h3 class="card-title">
        <button class="card-title-btn" type="button" data-open="${p.id}">${esc(p.name)}</button>
      </h3>
      <p class="rating">
        ${starsHTML(p.rating)}
        <span>${p.rating.toFixed(1)}</span>
        <span>(${countFmt.format(p.rating_count)})</span>
      </p>
      ${moneyHTML(p)}
      ${sw.length ? `<ul class="swatches" aria-label="Available colors">${sw
        .map((c) => `<li class="swatch" style="background:${COLOR_HEX[c]}" title="${c}"></li>`)
        .join("")}</ul>` : ""}
      <p class="${low ? "stock-note" : "ship-note"}">${low
        ? `Only ${p.stock} left`
        : freeShip(p) ? "Free shipping" : "Shipping from $5.95"}</p>
    </div>
  </article>`;
}

function esc(str) {
  return String(str).replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

/* ------------------------------------------------------------------- toasts */
let toastTimer;
function toast(message) {
  const el = $("#toast");
  el.textContent = message;
  el.hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { el.hidden = true; }, 2600);
}

/* ------------------------------------------------------------------ URL sync */
function readURL() {
  const p = new URLSearchParams(location.search);
  state.q = p.get("q") || "";
  state.cats = new Set((p.get("category") || "").split(",").filter(Boolean));
  state.minPrice = p.get("min_price") ? Number(p.get("min_price")) : null;
  state.maxPrice = p.get("max_price") ? Number(p.get("max_price")) : null;
  state.minRating = Number(p.get("min_rating") || 0);
  state.inStock = p.get("in_stock") === "1";
  state.sort = p.get("sort") || "trending";
  state.page = Number(p.get("page") || 1);
}

function writeURL(replace = false) {
  const p = new URLSearchParams();
  if (state.q) p.set("q", state.q);
  if (state.cats.size) p.set("category", [...state.cats].join(","));
  if (state.minPrice != null) p.set("min_price", state.minPrice);
  if (state.maxPrice != null) p.set("max_price", state.maxPrice);
  if (state.minRating) p.set("min_rating", state.minRating);
  if (state.inStock) p.set("in_stock", "1");
  if (state.sort !== "trending") p.set("sort", state.sort);
  if (state.page > 1) p.set("page", state.page);
  const qs = p.toString();
  const url = qs ? `?${qs}` : location.pathname;
  if (replace) history.replaceState({}, "", url);
}

function queryString(extra = {}) {
  const p = new URLSearchParams();
  if (state.q) p.set("q", state.q);
  if (state.cats.size) p.set("category", [...state.cats].join(","));
  if (state.minPrice != null) p.set("min_price", state.minPrice);
  if (state.maxPrice != null) p.set("max_price", state.maxPrice);
  if (state.minRating) p.set("min_rating", state.minRating);
  if (state.inStock) p.set("in_stock", "1");
  p.set("sort", state.sort === "relevance" && !state.q ? "trending" : state.sort);
  p.set("page", state.page);
  p.set("per_page", state.perPage);
  for (const [k, v] of Object.entries(extra)) p.set(k, v);
  return p.toString();
}

/* -------------------------------------------------------------- catalog load */
function skeletons(n = 8) {
  const dept = deptStyle("");
  $("#grid").innerHTML = Array.from({ length: n }).map(() => `
    <article class="card skeleton">
      <div class="thumb" style="--tint:${dept.tint}"></div>
      <div class="card-body">
        <div class="sk-line short"></div>
        <div class="sk-line"></div>
        <div class="sk-line short"></div>
      </div>
    </article>`).join("");
}

async function loadCatalog({ append = false } = {}) {
  if (!append) {
    state.page = 1;
    skeletons();
  }
  $("#resultCount").textContent = append ? $("#resultCount").textContent : "Loading…";

  const url = state.q ? `/api/search?${queryString()}` : `/api/catalog?${queryString()}`;
  let data;
  try {
    const res = await fetch(url);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    data = await res.json();
  } catch (err) {
    $("#grid").innerHTML = "";
    $("#resultCount").textContent = "Could not reach the catalogue API.";
    toast("Could not load products. Is the server running?");
    return;
  }

  state.total = data.total;
  state.items = append ? state.items.concat(data.items) : data.items;

  $("#grid").innerHTML = state.items.map(cardHTML).join("");
  $("#empty").hidden = state.total > 0;

  const latency = `${data.took_ms} ms`;
  $("#factLatency").textContent = latency;

  const shown = state.items.length;
  $("#resultCount").textContent = state.q
    ? `${countFmt.format(state.total)} result${state.total === 1 ? "" : "s"} for “${state.q}” · searched in ${latency}`
    : `${countFmt.format(state.total)} products · loaded in ${latency}`;

  $("#catalogTitle").textContent = state.q
    ? `Results for “${state.q}”`
    : state.cats.size === 1 ? [...state.cats][0] : "All Products";

  const note = $("#queryNote");
  const unknown = data.unknown_terms || [];
  const matched = data.matched_terms || [];
  const expansions = data.expansions || {};
  const expanded = Object.entries(expansions)
    .map(([term, words]) => `<b>${esc(term)}</b> → ${words.map(esc).join(", ")}`);
  if (state.q && (unknown.length || matched.length)) {
    note.hidden = false;
    note.innerHTML = [
      matched.length ? `Matched terms: <b>${matched.map(esc).join(", ")}</b>.` : "No catalogue term matched.",
      expanded.length ? `Autocompleted: ${expanded.join("; ")}.` : "",
      unknown.length ? `Not found: <b>${unknown.map(esc).join(", ")}</b>.` : "",
    ].filter(Boolean).join(" ");
  } else {
    note.hidden = true;
  }

  $("#loadMoreWrap").hidden = shown >= state.total;
  $("#loadNote").textContent = `Showing ${countFmt.format(shown)} of ${countFmt.format(state.total)} products`;
  $("#emptyNote").textContent = state.q
    ? `Nothing in the catalogue matches “${state.q}”. Try a broader term such as “headphones” or “cookware”.`
    : "Try removing a department, raising the price limit, or clearing the stock filter.";
}

/* ------------------------------------------------------------------- filters */
function renderFacets() {
  const f = state.facets;
  if (!f) return;

  $("#factProducts").textContent = countFmt.format(f.total_products);
  $("#factDepts").textContent = f.categories.length;

  $("#deptGrid").innerHTML = f.categories.map((c) => {
    const dept = deptStyle(c.name);
    const active = state.cats.has(c.name);
    return `
      <button class="dept-tile" type="button" data-dept="${esc(c.name)}"
        style="--tint:${dept.tint};--tint-ink:${dept.ink}" aria-pressed="${active}">
        ${iconSvg(dept.icon).replace("<svg", '<svg class="dept-icon"')}
        <span class="dept-name">${esc(c.name)}</span>
        <span class="dept-count">${c.count} products</span>
      </button>`;
  }).join("");

  $("#filterDepts").innerHTML = f.categories.map((c) => `
    <label class="check">
      <input type="checkbox" name="category" value="${esc(c.name)}" ${state.cats.has(c.name) ? "checked" : ""}>
      <span>${esc(c.name)}</span>
      <span class="check-num">${c.count}</span>
    </label>`).join("");

  const ratings = [4.5, 4, 3.5];
  $("#filterRating").innerHTML = ratings.map((r) => `
    <label class="check">
      <input type="radio" name="min_rating" value="${r}" ${state.minRating === r ? "checked" : ""}>
      <span>${r} stars &amp; up</span>
    </label>`).join("") + `
    <label class="check">
      <input type="radio" name="min_rating" value="0" ${state.minRating === 0 ? "checked" : ""}>
      <span>Any rating</span>
    </label>`;

  const max = Math.ceil(f.price_bounds.max);
  const range = $("#priceRange");
  range.max = max;
  range.value = state.maxPrice != null ? Math.min(state.maxPrice, max) : max;
  $("#priceMin").value = state.minPrice != null ? state.minPrice : "";
  $("#priceMax").value = state.maxPrice != null ? state.maxPrice : "";
  $("#rangeNote").textContent = `Up to ${money.format(Number(range.value))}`;

  $("#inStockToggle").checked = state.inStock;
  $("#sortSelect").value = state.sort;
  $("#searchInput").value = state.q;
  $("#searchClear").hidden = !state.q;
}

function syncFilterInputs() {
  const max = Math.ceil(state.facets?.price_bounds.max || 450);
  const range = $("#priceRange");
  range.value = state.maxPrice != null ? Math.min(state.maxPrice, max) : max;
  $$('input[name="category"]').forEach((el) => { el.checked = state.cats.has(el.value); });
  $$('input[name="min_rating"]').forEach((el) => { el.checked = Number(el.value) === state.minRating; });
  $("#inStockToggle").checked = state.inStock;
  $("#rangeNote").textContent = `Up to ${money.format(Number(range.value))}`;
  $$(".dept-tile").forEach((el) => el.setAttribute("aria-pressed", String(state.cats.has(el.dataset.dept))));
}

function applyAndReload() {
  writeURL(true);
  loadCatalog();
}

function toggleDept(name) {
  if (state.cats.has(name)) state.cats.delete(name);
  else state.cats.add(name);
  syncFilterInputs();
  applyAndReload();
}

function clearFilters() {
  state.cats.clear();
  state.minPrice = null;
  state.maxPrice = null;
  state.minRating = 0;
  state.inStock = false;
  state.sort = "trending";
  state.q = "";
  $("#searchInput").value = "";
  $("#searchClear").hidden = true;
  syncFilterInputs();
  applyAndReload();
  toast("Filters cleared.");
}

/* -------------------------------------------------------------- quick actions */
function quickAction(kind) {
  state.q = "";
  $("#searchInput").value = "";
  $("#searchClear").hidden = true;
  state.cats.clear();
  state.minPrice = null;
  state.maxPrice = null;
  state.minRating = 0;
  state.inStock = false;
  state.page = 1;

  if (kind === "new") state.sort = "newest";
  else if (kind === "best") state.sort = "rating";
  else if (kind === "under50") { state.sort = "trending"; state.maxPrice = 50; }
  else state.sort = "trending";

  if (window.innerWidth <= 1080) $("#mobileNav").hidden = true;
  syncFilterInputs();
  applyAndReload();
  $("#catalog").scrollIntoView({ behavior: "smooth", block: "start" });
}

/* ------------------------------------------------------------------- search */
let searchTimer;
let suggestIndex = -1;
let suggestItems = [];

async function runSuggestions(term) {
  const box = $("#searchResults");
  if (!term) {
    box.hidden = true;
    return;
  }
  let data = { items: [] };
  let terms = [];
  try {
    const [searchRes, suggestRes] = await Promise.all([
      fetch(`/api/search?q=${encodeURIComponent(term)}&per_page=5&sort=relevance`),
      fetch(`/api/suggest?q=${encodeURIComponent(term)}`),
    ]);
    data = await searchRes.json();
    terms = (await suggestRes.json()).suggestions || [];
  } catch {
    box.hidden = true;
    return;
  }

  suggestItems = [];
  const parts = [];

  if (data.items?.length) {
    parts.push('<p class="sr-group-label">Products</p>');
    data.items.forEach((p) => {
      const dept = deptStyle(p.category);
      suggestItems.push({ type: "product", id: p.id });
      parts.push(`
        <button class="sr-item" type="button" data-open="${p.id}" data-idx="${suggestItems.length - 1}">
          <span class="sr-thumb" style="--tint:${dept.tint};--tint-ink:${dept.ink}">${iconSvg(iconKeyFor(p))}</span>
          <span class="sr-text">
            <span class="sr-name">${esc(p.name)}</span>
            <span class="sr-meta">${esc(p.category)}</span>
          </span>
          <span class="sr-price">${money.format(p.price)}</span>
        </button>`);
    });
  }

  const extraTerms = terms.filter((t) => t.toLowerCase() !== term.toLowerCase() && t !== "").slice(0, 4);
  if (extraTerms.length) {
    parts.push('<p class="sr-group-label">Suggestions</p>');
    extraTerms.forEach((t) => {
      suggestItems.push({ type: "term", value: t });
      parts.push(`
        <button class="sr-item sr-term" type="button" data-term="${esc(t)}" data-idx="${suggestItems.length - 1}">
          <svg class="icon" viewBox="0 0 24 24" aria-hidden="true"><circle cx="10.5" cy="10.5" r="6.5"/><path d="M15.5 15.5L21 21"/></svg>
          <span>${esc(t)}</span>
        </button>`);
    });
  }

  if (!parts.length) {
    box.innerHTML = '<p class="sr-foot">No matches. Try “headphones”, “skillet” or “vitamin”.</p>';
    box.hidden = false;
    return;
  }

  const total = data.total ?? 0;
  parts.push(`<button class="sr-foot" type="button" data-term="${esc(term)}" style="width:100%;border:0;border-top:1px solid var(--line);cursor:pointer">
      Show all ${countFmt.format(total)} result${total === 1 ? "" : "s"} for “${esc(term)}”
    </button>`);
  box.innerHTML = parts.join("");
  box.hidden = false;
  suggestIndex = -1;
}

function highlightSuggestion(delta) {
  const rows = $$(".sr-item");
  if (!rows.length) return;
  suggestIndex = (suggestIndex + delta + rows.length) % rows.length;
  rows.forEach((r, i) => r.classList.toggle("is-active", i === suggestIndex));
  rows[suggestIndex].scrollIntoView({ block: "nearest" });
}

function chooseSuggestion() {
  const rows = $$(".sr-item");
  if (suggestIndex >= 0 && rows[suggestIndex]) rows[suggestIndex].click();
  else submitSearch($("#searchInput").value);
}

function submitSearch(term) {
  state.q = String(term || "").trim();
  state.page = 1;
  $("#searchResults").hidden = true;
  $("#searchClear").hidden = !state.q;
  $("#searchInput").value = state.q;
  applyAndReload();
  if (state.q) $("#catalog").scrollIntoView({ behavior: "smooth", block: "start" });
}

/* -------------------------------------------------------------------- rails */
async function loadRails() {
  try {
    const res = await fetch("/api/catalog?sort=trending&per_page=10");
    const data = await res.json();
    $("#trendingRail").innerHTML = data.items.map(cardHTML).join("");
  } catch {
    $("#trendingRail").innerHTML = "";
  }
  loadRecommendations();
}

async function loadRecommendations() {
  if (!state.viewed.length) return;
  try {
    const res = await fetch(`/api/recommend?viewed=${state.viewed.join(",")}&k=8`);
    const data = await res.json();
    if (!data.items?.length) return;
    $("#recoSub").textContent = `Built from the ${state.viewed.length} product${state.viewed.length === 1 ? "" : "s"} you opened.`;
    $("#recoRail").innerHTML = data.items.map((it) => cardHTML(it.product)).join("");
    $("#recoSection").hidden = false;
  } catch {
    /* keep the section hidden if the engine is unreachable */
  }
}

/* ------------------------------------------------------------------- product */
let qvOpen = false;
let qvOpener = null;

async function openProduct(id, { push = true } = {}) {
  let data;
  try {
    const res = await fetch(`/api/product/${id}`);
    if (!res.ok) throw new Error("not found");
    data = await res.json();
  } catch {
    toast("That product could not be loaded.");
    return;
  }

  const p = data.product;
  const dept = deptStyle(p.category);
  const similar = (data.similar || []).slice(0, 4);
  const soldOut = p.stock <= 0;
  const sw = swatches(p);

  trackView(id);

  $("#quickviewBody").innerHTML = `
    <div class="qv-grid">
      <div class="qv-gallery">
        <div class="qv-main" style="--tint:${dept.tint};--tint-ink:${dept.ink}">${p.image ? productImage(p, p.name) : iconSvg(iconKeyFor(p))}</div>
        ${
          p.image
            ? ""
            : `<div class="qv-thumbs" role="group" aria-label="Product image options">
          <button class="qv-thumb" type="button" aria-label="View on white" style="--tint-ink:${dept.ink}"><svg viewBox="0 0 32 32" aria-hidden="true">${ICONS[iconKeyFor(p)]}</svg></button>
          <button class="qv-thumb alt" type="button" aria-label="View on mist" style="--tint-ink:${dept.ink}"><svg viewBox="0 0 32 32" aria-hidden="true">${ICONS[iconKeyFor(p)]}</svg></button>
          <button class="qv-thumb alt2" type="button" aria-label="View on graphite" style="--tint-ink:${dept.ink}"><svg viewBox="0 0 32 32" aria-hidden="true">${ICONS[iconKeyFor(p)]}</svg></button>
        </div>`
        }
      </div>

      <div>
        <p class="qv-cat">${esc(p.category)} · ${esc(p.brand)}</p>
        <h2 class="qv-title" id="qvProductTitle">${esc(p.name)}</h2>
        <p class="qv-rating">
          ${starsHTML(p.rating)}
          <span>${p.rating.toFixed(1)}</span>
          <span>· ${countFmt.format(p.rating_count)} reviews</span>
          ${p.stock > 0 ? `<span>· ${p.stock} in stock</span>` : '<span class="stock-note">· Sold out</span>'}
        </p>
        <div class="qv-price">
          <span class="price-now">${money.format(p.price)}</span>
          ${onSale(p) ? `<s class="price-was">${money.format(compareAt(p))}</s><span class="price-off">Save ${discountPct(p)}%</span>` : ""}
        </div>
        <p class="qv-desc">${esc(p.description)}</p>

        ${sw.length ? `<div class="qv-block">
          <h3>Colors</h3>
          <ul class="swatches">
            ${sw.map((c) => `<li class="swatch" style="background:${COLOR_HEX[c]};width:20px;height:20px" title="${c}"></li>`).join("")}
          </ul>
        </div>` : ""}

        <div class="qv-block">
          <h3>Specifications</h3>
          <div class="qv-tags">${p.tags.map((t) => `<span class="qv-tag">${esc(t)}</span>`).join("")}</div>
        </div>

        <div class="qv-actions">
          <button class="btn btn-primary" type="button" data-add="${p.id}" ${soldOut ? "disabled" : ""}>
            ${soldOut ? "Sold Out" : "Add to Cart"}
          </button>
          <button class="btn btn-outline" type="button" data-quick="best">See Best Sellers</button>
        </div>

        <div class="qv-details">
          <details open>
            <summary>Shipping &amp; Delivery</summary>
            <p>Ships in 1–2 business days. Free over $75, otherwise $5.95 flat. Tracking is emailed when the label is created.</p>
          </details>
          <details>
            <summary>Returns &amp; Refunds</summary>
            <p>30 days from delivery, unused and in original packaging. Refunds are issued to the original payment method within five business days.</p>
          </details>
          <details>
            <summary>Materials &amp; Care</summary>
            <p>See the specification tags above. Most items are wipe-clean; textiles are machine washable at 30°C.</p>
          </details>
        </div>
      </div>
    </div>

    ${similar.length ? `<div class="qv-similar">
      <h3>You May Also Like</h3>
      <p class="qv-similar-sub">Ranked by item similarity, not by advertising.</p>
      <div class="qv-similar-grid">
        ${similar.map((s) => cardHTML(s.product)).join("")}
      </div>
    </div>` : ""}`;

  // name the dialog after the product now that the title exists
  document.querySelector(".modal-card").setAttribute("aria-labelledby", "qvProductTitle");
  if (!qvOpen) qvOpener = document.activeElement;
  $("#quickview").hidden = false;
  qvOpen = true;
  $("#closeQuickview").focus();

  if (push) {
    state.suppressHistory = true;
    history.pushState({ product: id }, "", `#product-${id}`);
  }
}

function closeProduct({ fromHistory = false } = {}) {
  if (!qvOpen) return;
  $("#quickview").hidden = true;
  qvOpen = false;
  if (!fromHistory && location.hash.startsWith("#product-")) {
    history.back();
  } else if (location.hash.startsWith("#product-")) {
    history.replaceState({}, "", location.pathname + location.search);
  }
  if (qvOpener && document.contains(qvOpener)) qvOpener.focus();
  qvOpener = null;
}

function trackView(id) {
  state.viewed = [id, ...state.viewed.filter((x) => x !== id)].slice(0, 12);
  sessionStorage.setItem("shopmind_viewed", JSON.stringify(state.viewed));
  loadRecommendations();
}

/* ---------------------------------------------------------------------- cart */
function loadCart() {
  try {
    state.cart = JSON.parse(localStorage.getItem("shopmind_cart") || "[]");
  } catch {
    state.cart = [];
  }
}

function saveCart() {
  localStorage.setItem("shopmind_cart", JSON.stringify(state.cart));
  renderCart();
}

async function addToCart(id) {
  const existing = state.cart.find((l) => l.id === id);
  if (existing) {
    existing.qty += 1;
    saveCart();
    toast(`${existing.name} — quantity ${existing.qty}`);
    return;
  }
  try {
    const res = await fetch(`/api/product/${id}`);
    const { product: p } = await res.json();
    state.cart.push({
      id,
      qty: 1,
      name: p.name,
      price: p.price,
      category: p.category,
      icon: iconKeyFor(p),
    });
    saveCart();
    toast(`${p.name} added to cart.`);
  } catch {
    toast("Could not add that item.");
  }
}

function cartSubtotal() {
  return state.cart.reduce((sum, l) => sum + l.price * l.qty, 0);
}

function renderCart() {
  const count = state.cart.reduce((n, l) => n + l.qty, 0);
  $("#cartCount").textContent = count;
  $("#cartTitleCount").textContent = count;
  $("#cartButton").setAttribute("aria-label", `Open cart, ${count} item${count === 1 ? "" : "s"}`);

  $("#cartEmpty").hidden = state.cart.length > 0;
  $("#cartFoot").hidden = state.cart.length === 0;

  $("#cartItems").innerHTML = state.cart.map((l) => {
    const dept = deptStyle(l.category);
    return `
    <li class="cart-item">
      <div class="cart-thumb" style="--tint:${dept.tint};--tint-ink:${dept.ink}">${iconSvg(l.icon)}</div>
      <div>
        <p class="cart-name">${esc(l.name)}</p>
        <p class="cart-variant">${esc(l.category)}</p>
        <div class="cart-row">
          <div class="qty">
            <button type="button" data-qty="${l.id}" data-delta="-1" aria-label="Decrease quantity of ${esc(l.name)}">−</button>
            <span>${l.qty}</span>
            <button type="button" data-qty="${l.id}" data-delta="1" aria-label="Increase quantity of ${esc(l.name)}">+</button>
          </div>
          <span class="cart-price">${money.format(l.price * l.qty)}</span>
        </div>
        <button class="cart-remove" type="button" data-remove="${l.id}">Remove</button>
      </div>
    </li>`;
  }).join("");

  const subtotal = cartSubtotal();
  $("#cartSubtotal").textContent = money.format(subtotal);
  $("#cartShipNote").textContent = subtotal >= 75
    ? "Free shipping applied at checkout."
    : `Add ${money.format(75 - subtotal)} more for free shipping.`;
}

function changeQty(id, delta) {
  const line = state.cart.find((l) => l.id === id);
  if (!line) return;
  line.qty += delta;
  if (line.qty <= 0) state.cart = state.cart.filter((l) => l.id !== id);
  saveCart();
}

function removeLine(id) {
  state.cart = state.cart.filter((l) => l.id !== id);
  saveCart();
}

/* ------------------------------------------------------------------ overlays */
function openCart() {
  $("#cartDrawer").hidden = false;
  $("#scrim").hidden = false;
  $("#closeCart").focus();
}
function closeCart() {
  $("#cartDrawer").hidden = true;
  if ($("#enginePanel").hidden) $("#scrim").hidden = true;
}
async function openEngine() {
  $("#enginePanel").hidden = false;
  $("#scrim").hidden = false;
  $("#closeEngine").focus();
  try {
    const data = await (await fetch("/api/facets")).json();
    const { trie, index, recommender } = data.dsa;
    const last = $("#factLatency").textContent;
    $("#engineBody").innerHTML = `
      <dl>
        <div class="eng-row"><dt>Products indexed</dt><dd>${countFmt.format(index.documents)}</dd></div>
        <div class="eng-row"><dt>Distinct index terms</dt><dd>${countFmt.format(index.terms)}</dd></div>
        <div class="eng-row"><dt>Posting list entries</dt><dd>${countFmt.format(index.postings)}</dd></div>
        <div class="eng-row"><dt>Autocomplete trie nodes</dt><dd>${countFmt.format(trie.nodes)}</dd></div>
        <div class="eng-row"><dt>Indexed phrases</dt><dd>${countFmt.format(trie.words)}</dd></div>
        <div class="eng-row"><dt>Item similarity vectors</dt><dd>${countFmt.format(recommender.item_vectors)}</dd></div>
        <div class="eng-row"><dt>Last query</dt><dd>${esc(last)}</dd></div>
      </dl>

      <div class="eng-section">
        <h3>How Each Part Works</h3>
        <ul class="eng-list">
          <li><b>Autocomplete — prefix trie</b>Typing walks a character trie and returns the most popular completions under that prefix. <code>O(P + K log K)</code></li>
          <li><b>Search — inverted index, BM25</b>Each query term looks up its posting list instead of scanning the catalogue, then ranks documents by term frequency and rarity. <code>O(matching postings)</code></li>
          <li><b>Ranking — bounded min-heap</b>Top results and the trending rail keep only the best K candidates while streaming scores. <code>O(N log K)</code></li>
          <li><b>Ordering — merge sort</b>Every sort option uses a stable merge sort, so equally scored products keep a stable order across pages. <code>O(N log N)</code></li>
          <li><b>Recommendations — cosine similarity</b>Each product becomes a sparse vector of its terms and tags; the feed blends cosine similarity to what you opened with department affinity and a trending prior.</li>
        </ul>
      </div>

      <div class="eng-section">
        <h3>Filters</h3>
        <ul class="eng-list">
          <li><b>Department, price, rating and stock</b>Applied server-side before ranking, so pagination counts stay accurate.</li>
          <li><b>Deep links</b>Filters and search live in the URL — copy the address bar to share an exact view.</li>
        </ul>
      </div>`;
  } catch {
    $("#engineBody").innerHTML = "<p>Could not load engine details.</p>";
  }
}
function closeEngine() {
  $("#enginePanel").hidden = true;
  if ($("#cartDrawer").hidden) $("#scrim").hidden = true;
}

function closeAllOverlays() {
  if (!$("#cartDrawer").hidden) closeCart();
  if (!$("#enginePanel").hidden) closeEngine();
  if (qvOpen) closeProduct();
  $("#searchResults").hidden = true;
  $("#mobileNav").hidden = true;
  $("#scrim").hidden = true;
}

/* -------------------------------------------------------------------- events */
document.addEventListener("click", (event) => {
  const el = event.target.closest("[data-add],[data-open],[data-quick],[data-dept],[data-term],[data-qty],[data-remove],[data-engine],[data-info]");
  if (!el) {
    if (!event.target.closest(".search")) $("#searchResults").hidden = true;
    return;
  }
  if (el.dataset.add) addToCart(Number(el.dataset.add));
  else if (el.dataset.open) openProduct(Number(el.dataset.open));
  else if (el.dataset.quick) quickAction(el.dataset.quick);
  else if (el.dataset.dept) toggleDept(el.dataset.dept);
  else if (el.dataset.term) submitSearch(el.dataset.term);
  else if (el.dataset.qty) changeQty(Number(el.dataset.qty), Number(el.dataset.delta));
  else if (el.dataset.remove) removeLine(Number(el.dataset.remove));
  else if (el.hasAttribute("data-engine")) openEngine();
  else if (el.dataset.info) toast("This demo store has no support pages yet.");
});

$("#searchForm").addEventListener("submit", (e) => {
  e.preventDefault();
  submitSearch($("#searchInput").value);
});

$("#searchInput").addEventListener("input", (e) => {
  const term = e.target.value.trim();
  $("#searchClear").hidden = !term;
  clearTimeout(searchTimer);
  searchTimer = setTimeout(() => runSuggestions(term), 180);
});

$("#searchInput").addEventListener("keydown", (e) => {
  if (e.key === "ArrowDown") { e.preventDefault(); highlightSuggestion(1); }
  else if (e.key === "ArrowUp") { e.preventDefault(); highlightSuggestion(-1); }
  else if (e.key === "Enter") {
    const rows = $$(".sr-item");
    if (suggestIndex >= 0 && rows[suggestIndex]) { e.preventDefault(); rows[suggestIndex].click(); }
  } else if (e.key === "Escape") {
    $("#searchResults").hidden = true;
    suggestIndex = -1;
  }
});

$("#searchClear").addEventListener("click", () => {
  $("#searchInput").value = "";
  $("#searchClear").hidden = true;
  state.q = "";
  applyAndReload();
  $("#searchInput").focus();
});

$("#sortSelect").addEventListener("change", (e) => {
  state.sort = e.target.value;
  state.page = 1;
  applyAndReload();
});

$("#inStockToggle").addEventListener("change", (e) => {
  state.inStock = e.target.checked;
  state.page = 1;
  applyAndReload();
});

$("#filterDepts").addEventListener("change", (e) => {
  const name = e.target.value;
  if (e.target.checked) state.cats.add(name);
  else state.cats.delete(name);
  state.page = 1;
  syncFilterInputs();
  applyAndReload();
});

$("#filterRating").addEventListener("change", (e) => {
  state.minRating = Number(e.target.value);
  state.page = 1;
  applyAndReload();
});

let rangeTimer;
$("#priceRange").addEventListener("input", (e) => {
  const value = Number(e.target.value);
  const max = Number(e.target.max);
  state.maxPrice = value >= max ? null : value;
  $("#priceMax").value = state.maxPrice != null ? state.maxPrice : "";
  $("#rangeNote").textContent = `Up to ${money.format(value)}`;
  clearTimeout(rangeTimer);
  rangeTimer = setTimeout(() => { state.page = 1; applyAndReload(); }, 220);
});

["#priceMin", "#priceMax"].forEach((sel) => {
  $(sel).addEventListener("change", () => {
    const min = $("#priceMin").value === "" ? null : Number($("#priceMin").value);
    const max = $("#priceMax").value === "" ? null : Number($("#priceMax").value);
    state.minPrice = Number.isFinite(min) ? min : null;
    state.maxPrice = Number.isFinite(max) ? max : null;
    syncFilterInputs();
    state.page = 1;
    applyAndReload();
  });
});

$("#clearFilters").addEventListener("click", clearFilters);
$("#emptyReset").addEventListener("click", clearFilters);
$("#filtersApply").addEventListener("click", () => {
  $("#filtersPanel").classList.remove("is-open");
  $("#filtersToggle").setAttribute("aria-expanded", "false");
});

$("#filtersToggle").addEventListener("click", () => {
  const panel = $("#filtersPanel");
  const open = panel.classList.toggle("is-open");
  $("#filtersToggle").setAttribute("aria-expanded", String(open));
  if (open) panel.scrollIntoView({ behavior: "smooth", block: "start" });
});

$("#loadMore").addEventListener("click", () => {
  state.page += 1;
  writeURL(true);
  loadCatalog({ append: true });
});

$("#cartButton").addEventListener("click", openCart);
$("#closeCart").addEventListener("click", closeCart);
$("#cartBrowse").addEventListener("click", () => { closeCart(); $("#catalog").scrollIntoView({ behavior: "smooth" }); });
$("#checkoutButton").addEventListener("click", () =>
  toast("Demo store — checkout is not connected."));
$("#engineButtonTop").addEventListener("click", openEngine);
$("#closeEngine").addEventListener("click", closeEngine);
$("#closeQuickview").addEventListener("click", () => closeProduct());
$("#scrim").addEventListener("click", closeAllOverlays);

$("#quickview").addEventListener("click", (e) => {
  if (e.target.id === "quickview") closeProduct();
});

$("#navToggle").addEventListener("click", () => {
  const nav = $("#mobileNav");
  const open = nav.hidden;
  nav.hidden = !open;
  $("#navToggle").setAttribute("aria-expanded", String(open));
});

$("#newsletterForm").addEventListener("submit", (e) => {
  e.preventDefault();
  $("#newsletterEmail").value = "";
  toast("Demo store — no emails are sent.");
});

document.addEventListener("keydown", (e) => {
  const typing = /^(INPUT|TEXTAREA|SELECT)$/.test(document.activeElement.tagName);
  if (e.key === "/" && !typing) {
    e.preventDefault();
    $("#searchInput").focus();
  }
  if (e.key === "Escape") {
    if (qvOpen) closeProduct();
    else if (!$("#cartDrawer").hidden) closeCart();
    else if (!$("#enginePanel").hidden) closeEngine();
    else if (!$("#mobileNav").hidden) { $("#mobileNav").hidden = true; $("#navToggle").setAttribute("aria-expanded", "false"); }
    else $("#searchResults").hidden = true;
  }
});

window.addEventListener("popstate", () => {
  readURL();
  if (location.hash.startsWith("#product-")) {
    const id = Number(location.hash.replace("#product-", ""));
    if (Number.isFinite(id)) openProduct(id, { push: false });
  } else if (qvOpen) {
    closeProduct({ fromHistory: true });
  } else {
    syncFilterInputs();
    loadCatalog();
  }
});

/* --------------------------------------------------------------------- boot */
async function boot() {
  readURL();
  loadCart();
  renderCart();
  try {
    state.viewed = JSON.parse(sessionStorage.getItem("shopmind_viewed") || "[]");
  } catch {
    state.viewed = [];
  }
  $("#year").textContent = String(new Date().getFullYear());

  try {
    state.facets = await (await fetch("/api/facets")).json();
    renderFacets();
  } catch {
    toast("Could not load catalogue filters.");
  }

  await loadCatalog();
  loadRails();

  if (location.hash.startsWith("#product-")) {
    const id = Number(location.hash.replace("#product-", ""));
    if (Number.isFinite(id)) openProduct(id, { push: false });
  }
}

boot();
