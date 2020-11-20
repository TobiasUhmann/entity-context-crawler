from eval.model import Model


class RankBasedEvaluator:
    def __init__(self, model: Model, ow_triples, ow_entities):
        self.model = model
        self.ow_triples = ow_triples
        self.ow_entities = ow_entities

    def evaluate(self):
        for ow_triple in self.ow_triples:
            pred_ow_triples_batch, pred_cw_ent_batch = self.model.predict([ow_triple[0]])
            pred_ow_triples = pred_ow_triples_batch[0]
            pred_cw_ent = pred_cw_ent_batch[0]
            if pred_cw_ent is not None:
                r_triples = [pred_ow_triple for pred_ow_triple in pred_ow_triples if pred_ow_triple[1] == ow_triple[1]]
                corrupted_scores = [-1 for _ in range(15000)]
                for r_triple in r_triples:
                    corrupted_scores[r_triple[2]] = self.model.score(r_triple)

                rank = 0
                true_score = self.model.score(ow_triple)
                for corrupted_score in corrupted_scores:
                    if corrupted_score >= true_score:
                        rank += 1

                print(rank)
