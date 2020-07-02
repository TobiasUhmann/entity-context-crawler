#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sqlite3
from dataclasses import dataclass
from typing import List, Tuple

from elasticsearch import Elasticsearch


class Model:
    def __init__(self, entity2id, triples):
        self.entity2id = entity2id
        self.triples = triples
        self.entity2id_rev = {entity: id for id, entity in entity2id.items()}

    def train(self, batch: List[Tuple[int, int, int]]):
        print('train')

    def predict(self, entity_ids: List[int]) -> List[List[Tuple[int, int, int]]]:
        """
        Takes all entities (closed world + open world) and predicts relations
        :param batch:
        :return:
        """

        es = Elasticsearch()
        with sqlite3.connect('data/enwiki-latest-test-contexts-30-300.db') as contexts_conn:

            result = []
            for count, entity_id in enumerate(entity_ids):
                if count % 100 == 0:
                    print(count)

                entity = self.entity2id[entity_id]
                test_contexts = select_test_contexts(contexts_conn, entity)

                mod_triples = set()
                if test_contexts:
                    test_context = test_contexts[0]
                    res = es.search(index="sentence-sampler-index",
                                    body={"query": {"match": {'context': test_context}}})

                    hit = res['hits']['hits'][0]
                    hit_entity = hit['_source']['entity']

                    if hit_entity not in self.entity2id_rev:
                        continue
                    hit_entity_id = self.entity2id_rev[hit_entity]

                    entity_triples = {(head, tail, tag) for head, tail, tag in self.triples
                                      if head == entity_id or tail == entity_id}

                    for entity_triple in entity_triples:
                        head, tail, tag = entity_triple
                        if head == entity_id:
                            head = hit_entity_id
                        if tail == entity_id:
                            tail = hit_entity_id
                        mod_triple = (head, tail, tag)
                        mod_triples.add(mod_triple)

                result.append(list(mod_triples))

        return result


@dataclass
class PredictResult:
    triples: List[Tuple[int, int, int]]
    scores: List[float]


def select_test_contexts(contexts_conn, entity):
    sql = '''
        SELECT context
        FROM contexts
        WHERE entity = ?
    '''

    cursor = contexts_conn.cursor()
    cursor.execute(sql, (entity,))
    rows = cursor.fetchall()
    cursor.close()

    return [row[0] for row in rows]
