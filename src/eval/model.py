from typing import List, Optional, Tuple


class Model:
    def train(self, batch: List[Tuple[int, int, int]]):
        """
        :param batch: List of (head, tail, rel) triples
        """

        raise NotImplementedError()

    def predict(self, query_entity_batch: List[int]) \
            -> Tuple[List[Optional[Tuple[int, int, int]]], List[Optional[int]]]:
        """
        Predict triples for a batch of open world entities.

        :param query_entity_batch: Batch of open world entities
        :return: Batch of triple lists, batch of most hit closed world entities
                 (for debugging)
        """

        raise NotImplementedError()
