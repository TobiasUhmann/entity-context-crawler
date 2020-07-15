#!/usr/bin/env python
# -*- coding: utf-8 -*-

from typing import List, Tuple, Set

from eval.classes import Result, TotalResult
from eval.model import Model


class Evaluator:
    def __init__(self,
                 model: Model,
                 actual_triples: Set[Tuple[int, int, int]],
                 entities: List[int]):

        self.model = model
        self.actual_triples = actual_triples
        self.entities = entities

    def run(self):
        results: List[Result] = []
        predicted_triples_batch, hit_entities = self.model.predict(self.entities)

        count = 0
        for entity, predicted_triples, hit_entity_id in zip(self.entities, predicted_triples_batch, hit_entities):
            if count % 100 == 0:
                print(count, count)

            actual_triples = {(head, tail, tag) for head, tail, tag in self.actual_triples
                              if head == entity or tail == entity}

            #
            # Calc precision, recall, F1
            #

            true_positives = 0
            false_positives = 0
            false_negatives = 0

            for predicted_triple in predicted_triples:
                if predicted_triple in actual_triples:
                    true_positives += 1
                else:
                    false_positives += 1

            for actual_triple in actual_triples:
                if actual_triple not in predicted_triples:
                    false_negatives += 1


            precision = true_positives / (true_positives + false_positives + 1e-9)
            recall = true_positives / (true_positives + false_negatives + 1e-9)
            f1 = 2 * (precision * recall) / (precision + recall + 1e-9)

            #
            # Calc AP
            #

            ranked_positives = 0
            ap_sum = 0
            for i, predicted_triple in enumerate(predicted_triples):
                rank = i + 1

                if predicted_triple in actual_triples:
                    ranked_positives += 1
                    ap_sum += ranked_positives / rank

            ap = ap_sum / (len(actual_triples) + 1e-10)

            #
            #
            #

            results.append(Result(hit_entity_id, predicted_triples, precision, recall, f1, ap))
            count += 1

        aps = [result.ap for result in results]
        mAP = sum(aps) / (len(aps) + 1e-10)

        return TotalResult(results, mAP)
