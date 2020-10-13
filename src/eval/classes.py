from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class Result:
    pred_ow_triples: List[Tuple[int, int, int]]
    precision: float
    recall: float
    f1: float
    ap: float

    # for debugging
    pred_cw_entity: str
    pred_ow_triples_hits: List[str]


@dataclass
class TotalResult:
    results: List[Result]
    map: float
