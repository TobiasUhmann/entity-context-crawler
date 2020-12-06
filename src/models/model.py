from typing import List, Optional, Tuple

from util.types import Triple


class Model:
    train_triples: List[Triple]

    def train(self, batch: List[Triple]):
        """
        :param batch: List of (head, tail, rel) triples
        """

        raise NotImplementedError()

    def score(self, triple):
        raise NotImplementedError()

    def predict(self, query_entity_batch: List[int]) \
            -> Tuple[List[List[Triple]], List[Optional[int]]]:
        """
        Predict triples for a batch of open world entities.

        :param query_entity_batch: Batch of open world entities
        :return: Batch of triple lists, batch of most hit closed world entities
                 (for debugging)
        """

        raise NotImplementedError()

    def predict_all_head_scores(self, rel: int, tail: int) -> List[float]:
        pass
