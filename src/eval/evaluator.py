from eval.classes import Result, TotalResult
from eval.model import Model


class Evaluator:
    def __init__(self, model: Model, ow_triples, ow_entities):
        self.model = model
        self.ow_triples = ow_triples
        self.ow_entity_batch = ow_entities

    def run(self):
        result_batch = []
        pred_ow_triples_batch, pred_cw_entity_batch = self.model.predict(self.ow_entity_batch)

        for query_entity, pred_entity, pred_triples in zip(self.ow_entity_batch, pred_cw_entity_batch,
                                                           pred_ow_triples_batch):

            actual_triples = {(head, tail, tag) for head, tail, tag in self.ow_triples
                              if head == query_entity or tail == query_entity}

            if pred_entity is None:
                result = Result(list(actual_triples),
                                precision=0,
                                recall=0,
                                f1=0,
                                ap=0,
                                pred_cw_entity='',
                                pred_ow_triples_hits=[' '] * len(actual_triples))

                result_batch.append(result)
                continue

            #
            # Calc precision, recall, F1
            #

            true_positives = 0
            false_positives = 0
            false_negatives = 0

            eval_triples = pred_triples + list(actual_triples.difference(set(pred_triples)))
            eval_triples_hits = []
            for eval_triple in eval_triples:
                if eval_triple in pred_triples and eval_triple in actual_triples:
                    true_positives += 1
                    eval_triples_hits.append('+')
                elif eval_triple in pred_triples and eval_triple not in actual_triples:
                    false_positives += 1
                    eval_triples_hits.append('-')
                elif eval_triple not in pred_triples and eval_triple in actual_triples:
                    false_negatives += 1
                    eval_triples_hits.append(' ')

            precision = true_positives / (true_positives + false_positives + 1e-9)
            recall = true_positives / (true_positives + false_negatives + 1e-9)
            f1 = 2 * (precision * recall) / (precision + recall + 1e-9)

            #
            # Calc AP
            #

            ranked_positives = 0
            ap_sum = 0
            for i, pred_triple in enumerate(pred_triples):
                rank = i + 1

                if pred_triple in actual_triples:
                    ranked_positives += 1
                    ap_sum += ranked_positives / rank

            ap = ap_sum / (len(actual_triples) + 1e-10)

            #
            #
            #

            result_batch.append(Result(eval_triples, precision, recall, f1, ap, pred_entity, eval_triples_hits))

        aps = [result.ap for result in result_batch]
        mAP = sum(aps) / (len(aps) + 1e-10)

        return TotalResult(result_batch, mAP)
