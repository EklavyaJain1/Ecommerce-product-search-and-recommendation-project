"""Sorting module: merge sort and quicksort used by the catalog sort control.

Merge sort: stable, O(N log N) worst case - used for price/rating sorts so
ties keep catalog order. Quicksort (median-of-3, insertion cutoff) provided
for comparison in the DSA inspector panel.
"""
from __future__ import annotations

from typing import Callable, List, Sequence, TypeVar

T = TypeVar("T")


def merge_sort(items: Sequence[T], key: Callable[[T], object], reverse: bool = False) -> List[T]:
    arr = list(items)

    def _ms(a: List[T]) -> List[T]:
        if len(a) <= 1:
            return a
        mid = len(a) // 2
        left = _ms(a[:mid])
        right = _ms(a[mid:])
        return _merge(left, right)

    def _merge(l: List[T], r: List[T]) -> List[T]:
        out: List[T] = []
        i = j = 0
        while i < len(l) and j < len(r):
            a, b = key(l[i]), key(r[j])
            take_left = (a <= b) if not reverse else (a >= b)
            if take_left:
                out.append(l[i])
                i += 1
            else:
                out.append(r[j])
                j += 1
        out.extend(l[i:])
        out.extend(r[j:])
        return out

    return _ms(arr)


def quick_sort(items: Sequence[T], key: Callable[[T], object], reverse: bool = False) -> List[T]:
    arr = list(items)

    def _qsort(lo: int, hi: int) -> None:
        if lo >= hi:
            return
        if hi - lo < 24:  # insertion sort cutoff for small slices
            for i in range(lo + 1, hi + 1):
                j = i
                while j > lo and _gt(arr[j], arr[j - 1]):
                    arr[j], arr[j - 1] = arr[j - 1], arr[j]
                    j -= 1
            return
        # median-of-3 pivot
        mid = (lo + hi) // 2
        trio = sorted([arr[lo], arr[mid], arr[hi]], key=key)
        pivot = trio[1]
        i, j = lo, hi
        while i <= j:
            while _gt(arr[i], pivot):
                i += 1
            while _gt(pivot, arr[j]):
                j -= 1
            if i <= j:
                arr[i], arr[j] = arr[j], arr[i]
                i += 1
                j -= 1
        _qsort(lo, j + 1)
        _qsort(i, hi)

    def _gt(x: T, y: T) -> bool:
        kx, ky = key(x), key(y)
        return (kx > ky) if not reverse else (kx < ky)

    _qsort(0, len(arr) - 1)
    return arr


ALGORITHMS = {
    "merge": ("Merge sort", "Stable O(N log N) - ties keep catalog order", merge_sort),
    "quick": ("Quicksort", "Median-of-3 + insertion cutoff, in-place partitioning", quick_sort),
}


def sort_items(items: List[T], key: Callable[[T], object], reverse: bool = False, algorithm: str = "merge") -> List[T]:
    fn = ALGORITHMS.get(algorithm, ALGORITHMS["merge"])[2]
    return fn(items, key=key, reverse=reverse)
