#!/usr/bin/env python
# -*- coding: utf-8 -*-

from typing import List, Tuple

from eval.model import Model


class Evaluator:
    def __init__(self,
                 model: Model,
                 triples: List[Tuple[int, int, int]],
                 entities: List[int],
                 batch_size: int):

        self.model = model
        self.triples = triples
        self.entities = entities
        self.batch_size = batch_size
