#!/usr/bin/env python
# -*- coding: utf-8 -*-

from dataclasses import dataclass
from typing import List, Tuple


class Model:
    def train(self, batch: List[Tuple[int, int, int]]):
        print('train')

    def predict(self, entities: List[int]) -> List[List[Tuple[int, int, int]]]:
        """
        Takes all entities (closed world + open world) and predicts relations
        :param batch:
        :return:
        """

        return len(entities) * [[(3, 2, 3), (3, 5, 3), (5, 3, 3)]]

@dataclass
class PredictResult:
    triples: List[Tuple[int, int, int]]
    scores: List[float]
