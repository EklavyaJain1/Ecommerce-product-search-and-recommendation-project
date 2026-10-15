"""Prefix Trie for live search-as-you-type suggestions.

Complexity: insert O(L), autocomplete O(P + K log K) where P is the number of
nodes under the prefix and K the number of completions harvested.
"""
from __future__ import annotations

import heapq
from typing import Dict, List, Tuple


class _Node:
    __slots__ = ("children", "terminal", "weight_sum")

    def __init__(self) -> None:
        self.children: Dict[str, "_Node"] = {}
        # (weight, word) pairs of words ending exactly here (deduped by word)
        self.terminal: Dict[str, float] = {}
        # aggregate popularity of every word passing through this node
        self.weight_sum: float = 0.0


class Trie:
    """Character trie ranking completions by weighted popularity."""

    def __init__(self) -> None:
        self.root = _Node()
        self.size = 0  # distinct words inserted
        self.node_count = 1

    def insert(self, word: str, weight: float = 1.0) -> None:
        word = word.strip().lower()
        if not word:
            return
        node = self.root
        for ch in word:
            if ch not in node.children:
                node.children[ch] = _Node()
                self.node_count += 1
            node = node.children[ch]
            node.weight_sum += weight
        if word not in node.terminal:
            self.size += 1
        node.terminal[word] = node.terminal.get(word, 0.0) + weight

    def autocomplete(self, prefix: str, limit: int = 8) -> List[Tuple[str, float]]:
        """Top-`limit` completions of `prefix` as (word, weight), best first.

        Uses a bounded min-heap over the subtree so we never materialise
        every candidate: O(P + K log K).
        """
        prefix = prefix.strip().lower()
        if not prefix:
            return []
        node = self.root
        for ch in prefix:
            if ch not in node.children:
                return []
            node = node.children[ch]

        heap: List[Tuple[float, str]] = []
        stack = [node]
        while stack:
            cur = stack.pop()
            for w, weight in cur.terminal.items():
                if len(heap) < limit:
                    heapq.heappush(heap, (weight, w))
                elif weight > heap[0][0]:
                    heapq.heapreplace(heap, (weight, w))
            for child in cur.children.values():
                stack.append(child)
        # heap entries are (weight, word); public contract is (word, weight)
        ordered = sorted(heap, key=lambda entry: entry[0], reverse=True)
        return [(word, weight) for weight, word in ordered]

    def stats(self) -> Dict[str, int]:
        return {"words": self.size, "nodes": self.node_count}
