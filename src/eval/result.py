#!/usr/bin/env python
# -*- coding: utf-8 -*-

from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class Result:
    triples: List[List[Tuple[int, int, int]]]
    mmr: float
