"""Recommendation engine: content cosine similarity + hybrid personalisation.

Vectors are sparse TF dicts over tokens/attributes. Cosine similarity between
two products: O(shared terms). "Also like" uses a TopKHeap over all pairwise
similarities; the personalised feed blends:
  0.55 * mean cosine similarity to recently viewed items (taste profile)
+ 0.25 * category affinity from the view history
+ 0.20 * trending score (global popularity prior)
"""
from __future__ import annotations

import math
from collections import Counter, defaultdict
from typing import Dict, List, Tuple

from .heaps import TopKHeap
from .inverted_index import tokenize

Vec = Dict[str, float]


def _cosine(a: Vec, b: Vec) -> float:
    if len(a) > len(b):
        a, b = b, a
    dot = sum(w * b.get(t, 0.0) for t, w in a.items())
    if dot == 0.0:
        return 0.0
    na = math.sqrt(sum(w * w for w in a.values()))
    nb = math.sqrt(sum(w * w for w in b.values()))
    return dot / (na * nb + 1e-9)


class Recommender:
    def __init__(self, products: List[dict]) -> None:
        self.products = {p["id"]: p for p in products}
        self.vectors: Dict[int, Vec] = {}
        self.trend_max = max((p.get("trending_score", 0.0) for p in products), default=1.0) or 1.0
        for p in products:
            vec: Counter = Counter()
            for t in tokenize(f"{p['name']} {p['type']} {' '.join(p['tags'])}"):
                vec[t] += 1.0
            vec[f"cat::{p['category'].lower().replace(' ', '_')}"] = 3.0
            for t in p["tags"]:
                vec[f"tag::{t}"] += 2.0
            self.vectors[p["id"]] = dict(vec)

    # ---------- item-item ----------
    def similar(self, pid: int, k: int = 6) -> List[Tuple[float, dict]]:
        base = self.vectors.get(pid)
        if not base:
            return []
        heap = TopKHeap(k)
        for other_id, vec in self.vectors.items():
            if other_id == pid:
                continue
            heap.offer(_cosine(base, vec), self.products[other_id])
        return heap.drain()

    # ---------- personalised hybrid ----------
    def recommend(
        self,
        viewed: List[int],
        k: int = 8,
        exclude: set | None = None,
    ) -> Tuple[List[Tuple[float, dict, str]], str]:
        """Returns ([(score, product, reason)], strategy)."""
        exclude = set(exclude or ()) | set(viewed)
        history = [pid for pid in viewed if pid in self.vectors][-12:]
        if not history:
            # cold start: pure trending board via heap
            heap = TopKHeap(k)
            for p in self.products.values():
                if p["id"] in exclude or p["stock"] <= 0:
                    continue
                heap.offer(p.get("trending_score", 0.0) / self.trend_max, p)
            return [
                (round(s, 4), it, "Trending now")
                for s, it in heap.drain()
            ], "cold-start trending"

        cat_w: Counter = Counter()
        for pid in history:
            cat_w[self.products[pid]["category"]] += 1.0
        cat_total = sum(cat_w.values()) or 1.0

        heap = TopKHeap(k)
        for pid, vec in self.vectors.items():
            if pid in exclude:
                continue
            p = self.products[pid]
            taste = sum(_cosine(self.vectors[h], vec) for h in history) / len(history)
            cat = cat_w.get(p["category"], 0.0) / cat_total
            trend = p.get("trending_score", 0.0) / self.trend_max
            in_stock = 1.0 if p["stock"] > 0 else 0.35
            score = (0.55 * taste + 0.25 * cat + 0.20 * trend) * in_stock
            reason = self._reason(p, history, taste, cat)
            heap.offer(score, (p, reason))

        results = []
        for s, (p, reason) in heap.drain():
            results.append((round(s, 4), p, reason))
        return results, f"hybrid over {len(history)} viewed"

    @staticmethod
    def _reason(p: dict, history: List[int], taste: float, cat: float) -> str:
        if taste >= 0.42:
            return "Matches your recent taste"
        if cat >= 0.5:
            return f"Popular in {p['category']}"
        if p["rating"] >= 4.6:
            return "Highly rated by shoppers"
        return "Trending with shoppers"

    def stats(self) -> Dict[str, int]:
        dims = sum(len(v) for v in self.vectors.values())
        return {"item_vectors": len(self.vectors), "vector_dims": dims}
