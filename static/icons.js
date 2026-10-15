/* Product illustration system.
   A single consistent duotone line-icon set on a 32x32 grid, mapped to
   product types by keyword. Replaces per-product emoji so the whole
   catalogue reads as one designed family. */
"use strict";

const ICONS = {
  earbuds: '<circle cx="10" cy="10.5" r="3.6"/><path d="M10 14.1V24"/><circle cx="22" cy="10.5" r="3.6"/><path d="M22 14.1V24"/>',
  headphones: '<path d="M5 18v-4a11 11 0 0122 0v4"/><rect x="3" y="17" width="5.5" height="9.5" rx="2.75"/><rect x="23.5" y="17" width="5.5" height="9.5" rx="2.75"/>',
  watch: '<rect x="9.5" y="9.5" width="13" height="13" rx="4"/><path d="M12.5 9.5V5.5h7v4M12.5 22.5v4h7v-4"/><path d="M16 13.5v3h2.5"/>',
  speaker: '<rect x="8.5" y="4.5" width="15" height="23" rx="3.5"/><circle cx="16" cy="11.5" r="3"/><circle cx="16" cy="21" r="3.6"/>',
  monitor: '<rect x="3.5" y="6.5" width="25" height="16" rx="2.5"/><path d="M12 27.5h8M16 22.5v5"/>',
  keyboard: '<rect x="3.5" y="10" width="25" height="13" rx="2.5"/><path d="M7.5 14h1.5M12 14h1.5M16.5 14h1.5M21 14h1.5M9 18.5h14"/>',
  mouse: '<rect x="11" y="5" width="10" height="22" rx="5"/><path d="M16 5.5v6.5M11.5 12h9"/>',
  battery: '<rect x="4.5" y="10" width="21" height="13" rx="3"/><path d="M28 14v5"/><path d="M14.5 13l-3.5 5.5h4L13.5 23"/>',
  laptop: '<rect x="7" y="7.5" width="18" height="12" rx="2"/><path d="M3.5 22.5h25l-1.5 3.5H5l-1.5-3.5Z"/>',
  camera: '<rect x="3.5" y="9.5" width="25" height="16" rx="3"/><circle cx="16" cy="17.5" r="4.2"/><path d="M11 9.5l1.8-3h6.4l1.8 3"/>',
  jacket: '<path d="M11 4.5l5 3 5-3 5.5 5-3 3.2V27.5H8.5V12.7l-3-3.2L11 4.5Z"/><path d="M16 7.5v20"/>',
  pants: '<path d="M9 5.5h14l1 22h-6.5L16 15l-1.5 12.5H8L9 5.5Z"/>',
  shirt: '<path d="M12 4.5l4 3 4-3 6 4-3 4.2V27.5H9V12.7L6 8.5l6-4Z"/>',
  shoe: '<path d="M4 20.5h24.5v4.5H4z"/><path d="M4 20.5l2.5-6.5h4l2-3h4l2.5 4c3 .6 6.5 2 8 5.5"/><path d="M13 14h3.5"/>',
  scarf: '<path d="M9 6.5c0-1.5 3-2.5 7-2.5s7 1 7 2.5-3 3-7 3-7-1.5-7-3Z"/><path d="M11 10v17M21 10v17"/><path d="M11 20h10"/>',
  glasses: '<circle cx="9.5" cy="17.5" r="5"/><circle cx="22.5" cy="17.5" r="5"/><path d="M14.5 16.5h3M4.5 15.5l1.5-4h4M27.5 15.5L26 11.5h-4"/>',
  bag: '<path d="M10 11.5V8.5a6 6 0 0112 0v3"/><rect x="5" y="11.5" width="22" height="16" rx="3"/><path d="M13.5 17.5h5"/>',
  dress: '<path d="M12.5 4.5h7l1.8 5.5-3 2 4.7 15.5H10l4.7-15.5-3-2 1.8-5.5Z"/>',
  plate: '<circle cx="16" cy="16" r="11"/><circle cx="16" cy="16" r="6"/>',
  pan: '<circle cx="13.5" cy="18.5" r="9.5"/><path d="M22.5 13.5l6.5-4"/>',
  fryer: '<rect x="7" y="8" width="18" height="20" rx="4"/><path d="M7 14h18"/><path d="M16 8V5.5"/><path d="M12 19h8"/>',
  appliance: '<rect x="6" y="7" width="20" height="21" rx="4"/><path d="M6 13.5h20"/><circle cx="11" cy="10.25" r="1.1"/><path d="M11.5 19h9M11.5 23h6"/>',
  candle: '<rect x="11" y="12" width="10" height="15" rx="2.5"/><path d="M16 12V8.5"/><path d="M16 8.5c2.2-1.6 2.2-3.6 0-5.5-2.2 1.9-2.2 3.9 0 5.5Z"/>',
  soft: '<rect x="3.5" y="12" width="25" height="12" rx="6"/><path d="M8.5 12c0-3.5 3.4-5.5 7.5-5.5s7.5 2 7.5 5.5"/>',
  lamp: '<path d="M8.5 14L16 4.5 23.5 14h-15Z"/><path d="M16 14v11M11 27.5h10"/>',
  bottle: '<path d="M12.5 4.5h7v3.6l2.5 4.2V26a2 2 0 01-2 2h-8a2 2 0 01-2-2V12.3l2.5-4.2V4.5Z"/><path d="M11.5 17h9"/>',
  lipstick: '<rect x="11.5" y="14" width="9" height="14" rx="2"/><path d="M13 14V9.5c1.5 1.2 3.5 1.2 6 .5V14"/>',
  perfume: '<rect x="9.5" y="12" width="13" height="16" rx="3"/><path d="M14 12V8.5h4V12"/><rect x="13" y="3.5" width="6" height="5" rx="1.5"/>',
  dryer: '<path d="M6.5 10.5h13a4.5 4.5 0 010 9h-8"/><rect x="3.5" y="7" width="12" height="16" rx="4"/><path d="M9.5 23l1.5 6h4l1.5-6"/>',
  nail: '<rect x="11.5" y="13" width="9" height="15" rx="3"/><path d="M14 13V8h4v5M16 8V4.5"/><path d="M13 20h6"/>',
  brush: '<path d="M16 4.5v10"/><path d="M12.5 14.5h7l-1 6h-5l-1-6Z"/><path d="M16 20.5v5"/>',
  yoga: '<rect x="3.5" y="17.5" width="25" height="9" rx="4.5"/><circle cx="8" cy="22" r="3.2"/>',
  bands: '<path d="M4 10c6-4 18-4 24 0"/><path d="M4 16c6-4 18-4 24 0"/><path d="M4 22c6-4 18-4 24 0"/>',
  weights: '<path d="M6 12.5v7M10.5 9v14M21.5 9v14M26 12.5v7M10.5 16h11"/>',
  tent: '<path d="M3 26h26L16 6.5 3 26Z"/><path d="M16 26l-4.2-9.5L16 11l4.2 5.5L16 26Z"/>',
  rope: '<rect x="3" y="4.5" width="4" height="9" rx="2"/><rect x="25" y="4.5" width="4" height="9" rx="2"/><path d="M5 13.5c0 10 22 10 22 0"/>',
  helmet: '<path d="M4.5 20a11.5 11.5 0 0123 0v3.5h-23V20Z"/><path d="M4.5 20h23M13.5 8.5V20"/><path d="M4.5 23.5v4M27.5 23.5v4"/>',
  book: '<path d="M16 9.5C12 6.5 7 6.5 4 7.5v16c3-1 8-1 12 2 4-3 9-3 12-2v-16c-3-1-8-1-12 2Z"/><path d="M16 9.5v16"/>',
  book2: '<path d="M8 5.5h13a3 3 0 013 3v18H11a3 3 0 01-3-3v-18Z"/><path d="M11.5 5.5v21"/><path d="M15.5 12.5h5.5M15.5 16.5h3.5"/>',
  book3: '<rect x="5" y="9" width="22" height="5.5" rx="1.2"/><rect x="7" y="15" width="18" height="5.5" rx="1.2"/><rect x="9" y="21" width="14" height="5" rx="1.2"/>',
  dropper: '<rect x="11.5" y="12" width="9" height="16" rx="2.5"/><path d="M14.5 12V7.5h3V12"/><path d="M16 7.5V4"/>',
  tube: '<rect x="12.5" y="9" width="7" height="19" rx="2"/><rect x="13.5" y="4" width="5" height="5" rx="1"/><path d="M12.5 15h7"/>',
  box: '<path d="M16 4.5l11 6v12l-11 6-11-6v-12l11-6Z"/><path d="M5 10.5l11 6 11-6M16 16.5v12"/>',
};

/* ordered matchers — first hit wins, so put specific terms before generic ones */
const ICON_RULES = [
  [/earbud/, "earbuds"],
  [/headphone|noise-cancel|over-ear/, "headphones"],
  [/watch|chrono/, "watch"],
  [/speaker/, "speaker"],
  [/monitor|streaming|smart tv|television/, "monitor"],
  [/keyboard|piano/, "keyboard"],
  [/mouse/, "mouse"],
  [/power bank|battery|charger/, "battery"],
  [/laptop/, "laptop"],
  [/camera|webcam/, "camera"],
  [/jacket|parka|coat/, "jacket"],
  [/jeans|pants|trousers/, "pants"],
  [/t-shirt|tee|shirt|top/, "shirt"],
  [/sneaker|shoe|runner|boot/, "shoe"],
  [/scarf|shawl/, "scarf"],
  [/sunglass|eyewear|glasses|goggle/, "glasses"],
  [/backpack|tote|handbag|bag|luggage/, "bag"],
  [/dress|gown/, "dress"],
  [/dinnerware|plate|dish|bowl/, "plate"],
  [/skillet|frying pan|\bpan\b|cookware/, "pan"],
  [/air fryer|fryer/, "fryer"],
  [/kettle|espresso|coffee|machine|vacuum|robot|blender|toaster/, "appliance"],
  [/candle/, "candle"],
  [/pillow|blanket|throw|cushion|duvet/, "soft"],
  [/lamp|light|lantern/, "lamp"],
  [/serum|essential oil|dropper/, "dropper"],
  [/sunscreen|moistur|lotion|balm|cleanser|sunblock/, "tube"],
  [/nail|polish|lacquer/, "nail"],
  [/lipstick|lip gloss|lip balm/, "lipstick"],
  [/parfum|perfume|fragrance|cologne/, "perfume"],
  [/hair dryer|straightener|styler/, "dryer"],
  [/shampoo|conditioner|shower gel|body wash|scrub|mask/, "bottle"],
  [/bottle|flask|tumbler|thermos/, "bottle"],
  [/brush|applicator/, "brush"],
  [/yoga|mat\b/, "yoga"],
  [/resistance|bands?$/, "bands"],
  [/dumbbell|kettlebell|weight/, "weights"],
  [/tent|camping shelter|sleeping/, "tent"],
  [/rope|jump/, "rope"],
  [/helmet/, "helmet"],
  [/book|novel|poetry|cookbook|biography|paperback|hardcover|trilogy|fiction|self-help|sci-fi|fantasy|mystery|business|guide|almanac|stories|atlas/, "book"],
];

const DEPARTMENTS = {
  "Electronics": { tint: "#E8EDF3", ink: "#3C4A5A", icon: "headphones" },
  "Fashion": { tint: "#F3ECE4", ink: "#6B5A47", icon: "shirt" },
  "Home & Kitchen": { tint: "#EDEFE9", ink: "#4C5A45", icon: "plate" },
  "Beauty": { tint: "#F4EAEC", ink: "#6E4A50", icon: "bottle" },
  "Sports & Outdoors": { tint: "#E7EFEA", ink: "#3E5748", icon: "yoga" },
  "Books": { tint: "#F0EDE6", ink: "#57503F", icon: "book" },
};

const FALLBACK_DEPT = { tint: "#F1F1EC", ink: "#5B6067", icon: "box" };

function matchIcon(text) {
  for (const [re, key] of ICON_RULES) {
    if (re.test(text)) return key;
  }
  return null;
}

/* Match the product type first — names carry colour words ("Cream", "Sky",
   "Olive") that would otherwise collide with cosmetic keywords. */
function iconKeyFor(product) {
  const type = String(product.type || "").toLowerCase();
  const name = String(product.name || "").toLowerCase();
  const key = matchIcon(type) || matchIcon(`${type} ${name}`) || "box";
  if (key === "book") {
    const shelf = ["book", "book2", "book3"];
    return shelf[Number(product.id || 0) % shelf.length];
  }
  return key;
}

function deptStyle(category) {
  return Object.prototype.hasOwnProperty.call(DEPARTMENTS, category)
    ? DEPARTMENTS[category]
    : FALLBACK_DEPT;
}

function iconSvg(key, className = "") {
  const cls = className ? ` class="${className}"` : "";
  return `<svg${cls} viewBox="0 0 32 32" aria-hidden="true">${ICONS[key] || ICONS.box}</svg>`;
}
