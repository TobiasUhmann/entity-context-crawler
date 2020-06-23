#!/usr/bin/env python
# -*- coding: utf-8 -*-

from typing import List, Tuple, Optional


class Model:
    def train(self, batch: List[Tuple[int, int, int]]):
        print('train')

    def predict(self, batch: List[int]) -> List[List[Tuple[int, int, int]]]:
        print('predict')
        return []
