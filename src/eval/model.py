#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sqlite3

from dataclasses import dataclass
from elasticsearch import Elasticsearch
from typing import List, Tuple


class Model:
    def __init__(self, es: Elasticsearch, triples):
        self.es = es
        self.triples = triples

    def train(self, batch: List[Tuple[int, int, int]]):
        print('train')

    def predict(self, entities):
        """
        Takes all entities (closed world + open world) and predicts relations
        :param batch:
        :return:
        """

        with sqlite3.connect('data/enwiki-latest-ow-contexts-100-500.db') as contexts_conn:

            result = []
            hit_entities = []

            for count, entity in enumerate(entities):
                if count == 100:
                    print(count)
                    break

                test_contexts = select_test_contexts(contexts_conn, entity)

                hit_entity = None
                mod_triples = []
                if test_contexts:
                    concated_test_contexts = ' '.join(test_contexts)[:1024]  # max ES query length == 1024
                    res = self.es.search(index="enwiki-latest-cw-contexts-100-500",
                                         body={"query": {"match": {'context': concated_test_contexts}}})

                    hits = res['hits']['hits']
                    for hit in hits[:1]:
                        hit_entity = hit['_source']['entity']

                        entity_triples = [(head, tail, tag) for head, tail, tag in self.triples
                                          if head == hit_entity or tail == hit_entity]

                        for entity_triple in entity_triples:
                            head, tail, tag = entity_triple
                            if head == hit_entity:
                                head = entity
                            if tail == hit_entity:
                                tail = entity
                            mod_triple = (head, tail, tag)
                            mod_triples.append(mod_triple)

                hit_entities.append(hit_entity)
                result.append(list(mod_triples))

        return result, hit_entities


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
