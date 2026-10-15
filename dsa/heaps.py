"""Binary heap used for top-K selection over score streams.

A bounded min-heap of size K keeps only the best candidates while scanning N
items: O(N log K) time, O(K) memory - vs sorting all N items at O(N log N).
Also used for the live "trending" board.
"""
from __future__ import annotations

import heapq
from typing import Callable, Dict, Iterable, List, Tuple


class TopKHeap:
    """Keeps the K largest (score, item) pairs seen so far."""

    def __init__(self, k: int) -> None:
        self.k = k
        self._heap: List[Tuple[float, int, dict]] = []  # (score, tiebreak, item)
        self.pushes = 0
        self.pops = 0
        self._seq = 0

    def offer(self, score: float, item: dict) -> None:
        self.pushes += 1
        entry = (score, self._seq, item)
        self._seq += 1
        if len(self._heap) < self.k:
            heapq.heappush(self._heap, entry)
        elif score > self._heap[0][0]:
            heapq.heapreplace(self._heap, entry)
            self.pops += 1

    def drain(self) -> List[Tuple[float, dict]]:
        """Best-first list of (score, item)."""
        return [
            (s, it)
            for s, _, it in sorted(self._heap, key=lambda e: (e[0], e[1]), reverse=True)
        ]


def heap_top_k(
    items: Iterable[dict],
    score_fn: Callable[[dict], float],
    k: int,
) -> List[Tuple[float, dict]]:
    """Functional wrapper: top-k of items by score_fn, best first."""
    heap = TopKHeap(k)
    for it in items:
        heap.offer(score_fn(it), it)
    return heap.drain()


def counters() -> Dict[str, int]:
    """Documentation helper describing heap cost model (shown in UI legend)."""
    return {"push": "O(log K)", "offer_all": "O(N log K)", "memory": "O(K)"}
