from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class Result:
    hit_entity_id: int
    predicted_triples: List[Tuple[int, int, int]]
    precision: float
    recall: float
    f1: float
    ap: float


@dataclass
class TotalResult:
    results: List[Result]
    map: float