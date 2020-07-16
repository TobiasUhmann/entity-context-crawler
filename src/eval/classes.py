from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class Result:
    pred_cw_entity: int
    pred_ow_triples: List[Tuple[int, int, int]]
    precision: float
    recall: float
    f1: float
    ap: float


@dataclass
class TotalResult:
    results: List[Result]
    map: float