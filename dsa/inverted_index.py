"""Inverted index with BM25 ranking over product text fields.

Build: O(total tokens). Query: O(union of posting lists) - touches only
postings for query terms instead of scanning all documents.
"""
from __future__ import annotations

import math
import re
from collections import Counter, defaultdict
from typing import Dict, List, Tuple

_TOKEN_RE = re.compile(r"[a-z0-9]+")
_STOP = {
    "the", "a", "an", "and", "or", "of", "for", "to", "in", "on",
    "with", "is", "it", "by", "at", "from", "this", "that", "best",
}

K1 = 1.4
B = 0.6


def tokenize(text: str) -> List[str]:
    return [t for t in _TOKEN_RE.findall(text.lower()) if t not in _STOP and len(t) > 1]


class InvertedIndex:
    """term -> {doc_id: weighted term frequency} plus BM25 statistics."""

    def __init__(self, k1: float = K1, b: float = B) -> None:
        self.k1 = k1
        self.b = b
        self.postings: Dict[str, Dict[int, float]] = defaultdict(dict)
        self.doc_len: Dict[int, int] = {}
        self.avg_len: float = 0.0
        self.n_docs: int = 0

    def add_document(self, doc_id: int, weighted_fields: List[Tuple[str, float]]) -> None:
        """weighted_fields: [(text, field_weight), ...] e.g. name x3, tags x2, desc x1."""
        tf: Counter = Counter()
        total = 0
        for text, weight in weighted_fields:
            for tok in tokenize(text):
                tf[tok] += weight
                total += 1
        if not tf:
            return
        for tok, w in tf.items():
            self.postings[tok][doc_id] = w
        self.doc_len[doc_id] = max(total, 1)
        self.n_docs += 1
        self.avg_len = (
            (self.avg_len * (self.n_docs - 1) + self.doc_len[doc_id]) / self.n_docs
        )

    def idf(self, term: str) -> float:
        n_q = len(self.postings.get(term, ()))
        return math.log(1 + (self.n_docs - n_q + 0.5) / (n_q + 0.5))

    def search(
        self,
        query: str,
        limit: int = 60,
        prefix_provider=None,
        prefix_weight: float = 0.5,
    ) -> Tuple[List[Tuple[int, float]], List[str], List[str], Dict[str, List[str]]]:
        """Returns ([(doc_id, score)], matched_terms, unknown_terms, expansions).

        `prefix_provider(term) -> [(word, weight), ...]` supplies prefix
        completions from the autocomplete trie, so a partial word such as
        "head" still reaches documents indexed under "headphones". Expanded
        terms score at `prefix_weight` so exact matches always outrank them.
        """
        terms = tokenize(query)
        if not terms:
            return [], [], [], {}
        scores: Dict[int, float] = defaultdict(float)
        matched: List[str] = []
        unknown: List[str] = []
        expansions: Dict[str, List[str]] = {}

        def add(term: str, factor: float) -> None:
            idf = self.idf(term) * factor
            for doc_id, tf in self.postings[term].items():
                norm = self.k1 * (
                    1 - self.b + self.b * self.doc_len[doc_id] / max(self.avg_len, 1e-9)
                )
                scores[doc_id] += idf * (tf * (self.k1 + 1)) / (tf + norm)

        for term in terms:
            if term in self.postings:
                matched.append(term)
                add(term, 1.0)
                continue
            completions: List[str] = []
            if prefix_provider is not None:
                for word, _weight in prefix_provider(term):
                    if word in self.postings and word not in completions:
                        completions.append(word)
            if completions:
                matched.append(term)
                expansions[term] = completions[:4]
                for word in completions[:4]:
                    add(word, prefix_weight)
            else:
                unknown.append(term)

        ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)[:limit]
        return [(d, round(s, 4)) for d, s in ranked], matched, unknown, expansions

    def stats(self) -> Dict[str, int]:
        return {
            "terms": len(self.postings),
            "postings": sum(len(p) for p in self.postings.values()),
            "documents": self.n_docs,
        }
