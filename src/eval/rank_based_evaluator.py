from typing import List

from pykeen.evaluation import RankBasedMetricResults

from eval.model import Model
from util.custom_types import Triple


class RankBasedEvaluator:
    def evaluate(self, model: Model, test_triples: List[Triple]) -> RankBasedMetricResults:
        all_pos_triples = model.train_triples + test_triples

        metrics = []

        #
        # Head prediction
        #

        for test_triple in test_triples:
            all_head_scores = model.predict_all_head_scores(rel=test_triple[1], tail=test_triple[2])
            true_head_score = all_head_scores[test_triple[0]]

            #
            # Filter
            #

            pos_triples = [pos_triple for pos_triple in all_pos_triples
                           if pos_triple[1] == test_triple[1] and pos_triple[2] == test_triple[2]]

            for pos_triple in pos_triples:
                all_head_scores[pos_triple[0]] = float('nan')

            best_rank = 0
            worst_rank = 0

            for head_score in all_head_scores:
                if head_score > true_head_score:
                    best_rank += 1

                if head_score >= true_head_score:
                    worst_rank += 1

            metrics.append({'best_rank': best_rank, 'worst_rank': worst_rank})

        return metrics
