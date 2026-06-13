"""Palate read-model — predicts a bean's likely tasting outcome from similar past brews.

Content-based weighted KNN over the journal: each rated entry's frozen
`bean_dimensions_snapshot` is compared to the query bean; neighbours are weighted by
(1 - distance) and their tasting axes averaged. Exact brute-force — at personal scale
(hundreds of brews) there is no need for ANN/vector indexes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import builtins

    from brew.journal.model.entry import JournalEntry
    from brew.journal.repository import JournalRepository

_AXES = ("acidity", "bitterness", "body", "sweetness", "strength")
_WEIGHTS = {
    "varietal": 0.30,
    "process": 0.30,
    "roast_level": 0.20,
    "origin": 0.10,
    "altitude_masl": 0.05,
    "flavor_tags": 0.05,
}
_ROAST_ORDER = {"light": 0, "medium-light": 1, "medium": 2, "medium-dark": 3, "dark": 4}
_SIMILARITY_THRESHOLD = 0.25
_MIN_NEIGHBOURS = 2
_FULL_CONFIDENCE_SIM = 3.0


@dataclass(frozen=True)
class BeanDimensions:
    varietal: str | None = None
    process: str | None = None
    roast_level: str | None = None
    origin: str | None = None
    altitude_masl: int | None = None
    flavor_tags: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class PalateTendency:
    tendency: dict[str, float]
    confidence: float
    n: int
    neighbours: list[dict]


def _categorical(a: str | None, b: str | None) -> float:
    if a is None and b is None:
        return 0.0  # both absent — no mismatch
    if a is None or b is None:
        return 0.5  # one known, one unknown — partial penalty
    return 0.0 if a.lower() == b.lower() else 1.0


def _roast_distance(a: str | None, b: str | None) -> float:
    if a is None and b is None:
        return 0.0  # both absent — no mismatch
    if a is None or b is None:
        return 0.5
    ai, bi = _ROAST_ORDER.get(a.lower()), _ROAST_ORDER.get(b.lower())
    if ai is None or bi is None:
        return _categorical(a, b)
    return abs(ai - bi) / (len(_ROAST_ORDER) - 1)


def _altitude_distance(a: int | None, b: int | None) -> float:
    if a is None and b is None:
        return 0.0  # both absent — no mismatch
    if a is None or b is None:
        return 0.5  # one known, one unknown — partial penalty
    return min(1.0, abs(a - b) / 1000.0)


def _tag_distance(a: builtins.list[str], b: builtins.list[str]) -> float:
    if not a and not b:
        return 0.0  # both absent — no mismatch
    if not a or not b:
        return 0.5  # one known, one unknown — partial penalty
    sa, sb = {t.lower() for t in a}, {t.lower() for t in b}
    return 1.0 - len(sa & sb) / len(sa | sb)


def dimension_distance(
    query: BeanDimensions, snapshot: dict, query_tags: builtins.list[str], entry_tags: builtins.list[str]
) -> float:
    """Weighted sum of per-feature distances in [0, 1]."""
    parts = {
        "varietal": _categorical(query.varietal, snapshot.get("varietal")),
        "process": _categorical(query.process, snapshot.get("process")),
        "roast_level": _roast_distance(query.roast_level, snapshot.get("roast_level")),
        "origin": _categorical(query.origin, snapshot.get("origin")),
        "altitude_masl": _altitude_distance(query.altitude_masl, snapshot.get("altitude_masl")),
        "flavor_tags": _tag_distance(query_tags, entry_tags),
    }
    return sum(_WEIGHTS[k] * v for k, v in parts.items())


class PalateQuery:
    def __init__(self, repo: JournalRepository) -> None:
        self._repo = repo

    async def tendency_for(self, query: BeanDimensions, *, limit: int = 500) -> PalateTendency:
        entries = await self._repo.list(rating_min=1, limit=limit)
        scored: list[tuple[float, JournalEntry]] = []
        for e in entries:
            if e.bean_dimensions_snapshot is None:
                continue
            dist = dimension_distance(query, e.bean_dimensions_snapshot, query.flavor_tags, e.flavor_tags)
            sim = 1.0 - dist
            if sim >= _SIMILARITY_THRESHOLD:
                scored.append((sim, e))

        if len(scored) < _MIN_NEIGHBOURS:
            return PalateTendency(tendency={}, confidence=0.0, n=len(scored), neighbours=[])

        total_sim = sum(sim for sim, _ in scored)
        tendency: dict[str, float] = {}
        for axis in _AXES:
            weighted = [(sim, getattr(e, axis)) for sim, e in scored if getattr(e, axis) is not None]
            axis_total = sum(sim for sim, _ in weighted)
            if axis_total > 0:
                tendency[axis] = round(sum(sim * val for sim, val in weighted) / axis_total, 2)

        confidence = round(min(1.0, total_sim / _FULL_CONFIDENCE_SIM), 2)
        neighbours = [
            {
                "entry_id": e.id,
                "similarity": round(sim, 2),
                "axes": {a: getattr(e, a) for a in _AXES},
                "rating": e.rating,
            }
            for sim, e in sorted(scored, key=lambda x: x[0], reverse=True)
        ]
        return PalateTendency(tendency=tendency, confidence=confidence, n=len(scored), neighbours=neighbours)
