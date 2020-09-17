from typing import List, Optional, Tuple

from types import Entity, Triple


class Model:
    def train(self, batch: List[Triple]):
        """
        :param batch: List of (head, tail, rel) triples
        """

        raise NotImplementedError()

    def predict(self, query_entity_batch: List[Entity]) \
            -> Tuple[List[Optional[Triple]], List[Optional[Entity]]]:
        """
        Predict triples for a batch of open world entities.

        :param query_entity_batch: Batch of open world entities
        :return: Batch of triple lists, batch of most hit closed world entities
                 (for debugging)
        """

        raise NotImplementedError()
