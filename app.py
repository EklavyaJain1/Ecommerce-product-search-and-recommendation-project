"""ShopMind - ecommerce search & recommendation engine (Flask + DSA).

Endpoints
  GET /                       SPA shell
  GET /api/catalog            full catalog (sorted/filtered, heap-paginated)
  GET /api/search?q=          inverted-index BM25 search + trie suggestions
  GET /api/suggest?q=         trie autocomplete only (as-you-type)
  GET /api/product/<id>       product detail + "also like" neighbours
  GET /api/recommend?viewed=  personalised hybrid feed
  GET /api/facets             categories / price bounds / DSA stats
"""
from __future__ import annotations

import math
import time
from pathlib import Path

from flask import Flask, jsonify, render_template, request

from dsa.heaps import TopKHeap
from dsa.inverted_index import InvertedIndex
from dsa.recommender import Recommender
from dsa.sorting import sort_items
from dsa.trie import Trie

BASE = Path(__file__).parent

app = Flask(__name__, static_folder="static", template_folder="templates")

# ---------------------------------------------------------------- load & index
import json

PRODUCTS = json.loads((BASE / "data" / "products.json").read_text(encoding="utf-8"))
BY_ID = {p["id"]: p for p in PRODUCTS}

index = InvertedIndex()
trie = Trie()
for p in PRODUCTS:
    index.add_document(
        p["id"],
        [
            (f"{p['name']} {p['name']}", 3.0),
            (f"{p['brand']} {p['type']} {p['category']}", 2.0),
            (" ".join(p["tags"]), 2.0),
            (p["description"], 1.0),
        ],
    )
    weight = 1.0 + p["rating"] * p["rating_count"] / 4000.0
    for word in set(p["name"].lower().split()):
        if len(word) > 2:
            trie.insert(word, weight)
    trie.insert(p["type"].lower(), weight)
    for tag in p["tags"]:
        trie.insert(tag, weight * 0.8)

reco = Recommender(PRODUCTS)
CATS = sorted({p["category"] for p in PRODUCTS})
PRICE_MIN = min(p["price"] for p in PRODUCTS)
PRICE_MAX = max(p["price"] for p in PRODUCTS)

SORT_KEYS = {
    "relevance": (lambda p: p.get("_score", 0.0), True),
    "price_asc": (lambda p: p["price"], False),
    "price_desc": (lambda p: p["price"], True),
    "rating": (lambda p: p["rating"], True),
    "trending": (lambda p: p.get("trending_score", 0.0), True),
    "newest": (lambda p: -p["age_days"], False),
}

# ---------------------------------------------------------------- helpers


def decorate(items, scores=None):
    scores = scores or {}
    out = []
    for p in items:
        q = dict(p)
        q["_score"] = round(scores.get(p["id"], 0.0), 4)
        out.append(q)
    return out


def apply_facets(items, cats, pmin, pmax, rating_min, in_stock):
    if cats:
        wanted = set(cats)
        items = [p for p in items if p["category"] in wanted]
    if pmin is not None:
        items = [p for p in items if p["price"] >= pmin]
    if pmax is not None:
        items = [p for p in items if p["price"] <= pmax]
    if rating_min:
        items = [p for p in items if p["rating"] >= rating_min]
    if in_stock:
        items = [p for p in items if p["stock"] > 0]
    return items


def to_float(value, default=None):
    """Parse a query-string number, tolerating junk and non-finite values."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    return number if math.isfinite(number) else default


def to_int(value, default=0):
    """Parse a query-string integer, falling back instead of raising."""
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return default


def parse_common(args):
    cats = [c for c in (args.get("category") or "").split(",") if c]
    pmin = to_float(args.get("min_price"))
    pmax = to_float(args.get("max_price"))
    rating_min = to_float(args.get("min_rating"), 0.0) or 0.0
    in_stock = args.get("in_stock") == "1"
    sort = args.get("sort") or "relevance"
    page = max(to_int(args.get("page"), 1), 1)
    per_page = min(max(to_int(args.get("per_page"), 24), 6), 60)
    return cats, pmin, pmax, rating_min, in_stock, sort, page, per_page


# ---------------------------------------------------------------- routes


@app.get("/")
def home():
    return render_template("index.html")


@app.get("/api/catalog")
def api_catalog():
    t0 = time.perf_counter()
    cats, pmin, pmax, rating_min, in_stock, sort, page, per_page = parse_common(request.args)
    items = apply_facets(decorate(PRODUCTS), cats, pmin, pmax, rating_min, in_stock)
    key, rev = SORT_KEYS.get(sort, SORT_KEYS["trending"])
    items = sort_items(items, key=key, reverse=rev, algorithm="merge")
    total = len(items)
    start = (page - 1) * per_page
    page_items = items[start : start + per_page]
    return jsonify(
        {
            "items": page_items,
            "total": total,
            "page": page,
            "per_page": per_page,
            "took_ms": round((time.perf_counter() - t0) * 1000, 2),
            "algorithm": "Merge sort O(N log N)",
        }
    )


@app.get("/api/search")
def api_search():
    t0 = time.perf_counter()
    q = (request.args.get("q") or "").strip()
    cats, pmin, pmax, rating_min, in_stock, sort, page, per_page = parse_common(request.args)
    scored, matched, unknown, expansions = index.search(
        q, limit=400, prefix_provider=lambda t: trie.autocomplete(t, 4)
    )
    scores = dict(scored)
    hits = [BY_ID[d] for d, _ in scored if d in BY_ID]
    hits = apply_facets(decorate(hits, scores), cats, pmin, pmax, rating_min, in_stock)
    if sort == "relevance":
        hits = sort_items(hits, key=lambda p: p["_score"], reverse=True, algorithm="merge")
    else:
        key, rev = SORT_KEYS.get(sort, SORT_KEYS["trending"])
        hits = sort_items(hits, key=key, reverse=rev, algorithm="merge")
    total = len(hits)
    start = (page - 1) * per_page
    suggestions = [word for word, _ in trie.autocomplete(q.split()[-1] if q else "", 6)] if q else []
    return jsonify(
        {
            "items": hits[start : start + per_page],
            "total": total,
            "page": page,
            "per_page": per_page,
            "took_ms": round((time.perf_counter() - t0) * 1000, 2),
            "matched_terms": matched,
            "unknown_terms": unknown,
            "expansions": expansions,
            "suggestions": suggestions,
            "algorithm": "BM25 over inverted index",
        }
    )


@app.get("/api/suggest")
def api_suggest():
    q = (request.args.get("q") or "").strip().lower()
    if not q:
        return jsonify({"suggestions": []})
    words = [word for word, _ in trie.autocomplete(q, 8)]
    return jsonify({"suggestions": words, "prefix": q})


@app.get("/api/product/<int:pid>")
def api_product(pid: int):
    p = BY_ID.get(pid)
    if not p:
        return jsonify({"error": "not found"}), 404
    neighbours = [
        {"score": round(s, 4), "product": prod}
        for s, prod in reco.similar(pid, k=6)
    ]
    return jsonify({"product": p, "similar": neighbours, "algorithm": "Item-item cosine similarity"})


@app.get("/api/recommend")
def api_recommend():
    t0 = time.perf_counter()
    viewed = [int(x) for x in (request.args.get("viewed") or "").split(",") if x.strip().isdigit()][:40]
    k = min(max(to_int(request.args.get("k"), 8), 3), 16)
    results, strategy = reco.recommend(viewed, k=k)
    items = [
        {"score": s, "product": p, "reason": r}
        for s, p, r in results
    ]
    return jsonify(
        {
            "items": items,
            "strategy": strategy,
            "took_ms": round((time.perf_counter() - t0) * 1000, 2),
            "algorithm": "Hybrid: 0.55 taste + 0.25 category + 0.20 trending",
        }
    )


@app.get("/api/facets")
def api_facets():
    from dsa.heaps import counters as heap_cost

    cat_counts = {}
    for p in PRODUCTS:
        cat_counts[p["category"]] = cat_counts.get(p["category"], 0) + 1
    return jsonify(
        {
            "categories": [{"name": c, "count": cat_counts[c]} for c in CATS],
            "price_bounds": {"min": PRICE_MIN, "max": PRICE_MAX},
            "total_products": len(PRODUCTS),
            "dsa": {
                "trie": trie.stats(),
                "index": index.stats(),
                "recommender": reco.stats(),
                "heap_cost": heap_cost(),
            },
        }
    )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
