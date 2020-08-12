import random
import sqlite3

from collections import Counter
from elasticsearch import Elasticsearch
from typing import List, Tuple, Dict, Set, Optional

from dao.test_contexts import select_contexts


class BaselineModel:
    def __init__(self,
                 es: Elasticsearch,
                 es_index: str,
                 ow_contexts_db: str,
                 id2ent: Dict[int, str],
                 ent2id: Dict[str, int],
                 gt_triples: Set[Tuple[int, int, int]]):
        """
        :param es: ES index containing closed world contexts
        :param ow_contexts_db: DB containing open world contexts
        :param id2ent: {entity ID -> entity name} mapping
        :param gt_triples: List of ground truth (head, tail, rel) triples
        """

        self.es = es
        self.es_index = es_index
        self.query_contexts_db = ow_contexts_db
        self.id2ent = id2ent
        self.ent2id = ent2id
        self.gt_triples = list(gt_triples)

        #
        # Rank triples by (<head importance> + <tail importance>)
        #

        head_counter = Counter([head for head, _, _ in self.gt_triples])
        tail_counter = Counter([tail for _, tail, _ in self.gt_triples])

        self.gt_triples.sort(key=lambda t: head_counter[t[0]] + tail_counter[t[1]], reverse=True)

    def train(self, batch: List[Tuple[int, int, int]]):
        """
        :param batch: List of (head, tail, rel) triples
        """

        pass

    def predict(self, query_entity_batch: List[int]) \
            -> Tuple[List[Optional[Tuple[int, int, int]]], List[Optional[int]]]:
        """
        Predict triples for a batch of open world entities.

        Prediction for an entity:
        - Query ES index for most similar closed world entity
        - Get closed world entity's triples and replace closed world entity with open world query entity
        - Return modified triples as predicted triples

        :param query_entity_batch: Batch of open world entities
        :return: Batch of triple lists, batch of most hit closed world entities (for debugging)
        """

        with sqlite3.connect(self.query_contexts_db) as query_contexts_conn:

            # Optional as None is appended if no query context is available
            pred_triples_batch: List[Optional[List[Tuple[int, int, int]]]] = []
            hit_entity_batch: List[Optional[int]] = []

            for count, query_entity, in enumerate(query_entity_batch):

                query_entity_name = self.id2ent[query_entity]
                query_entity_contexts = select_contexts(query_contexts_conn, query_entity_name, random=False)
                random.shuffle(query_entity_contexts)

                if not query_entity_contexts:
                    print('[WARNING] No context for query entity "%s"' % query_entity_name)
                    hit_entity_batch.append(None)
                    pred_triples.append(None)

                else:
                    concated_query_entity_contexts = ' '.join(query_entity_contexts)[:1024]
                    es_result = self.es.search(index=self.es_index,
                                               body={'query': {'match': {'context': concated_query_entity_contexts}}})

                    es_hits = es_result['hits']['hits']
                    for es_hit in es_hits[:1]:
                        hit_entity_name = es_hit['_source']['entity']
                        hit_entity = self.ent2id[hit_entity_name]

                        hit_entity_triples = [(head, tail, rel) for head, tail, rel in self.gt_triples
                                              if head == hit_entity or tail == hit_entity]

                        pred_triples = [(query_entity if head == hit_entity else head,
                                         query_entity if tail == hit_entity else tail,
                                         rel)
                                        for head, tail, rel in hit_entity_triples]

                        hit_entity_batch.append(hit_entity)
                        pred_triples_batch.append(pred_triples)

        return pred_triples_batch, hit_entity_batch
