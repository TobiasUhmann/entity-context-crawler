#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sqlite3
from dataclasses import dataclass
from typing import List, Tuple

from elasticsearch import Elasticsearch


class Model:
    def __init__(self, triples):
        self.triples = triples

    def train(self, batch: List[Tuple[int, int, int]]):
        print('train')

    def predict(self, entities):
        """
        Takes all entities (closed world + open world) and predicts relations
        :param batch:
        :return:
        """

        es = Elasticsearch()
        with sqlite3.connect('data/enwiki-latest-test-contexts-30-500.db') as contexts_conn:

            result = []
            hit_entities = []

            for count, entity in enumerate(entities):
                if count == 100:
                    print(count)
                    break

                test_contexts = select_test_contexts(contexts_conn, entity)

                mod_triples = set()
                if test_contexts:
                    concated_test_contexts = ' '.join(test_contexts)[:1024]  # max ES query length == 1024
                    res = es.search(index="enwiki-latest-contexts-70-500",
                                    body={"query": {"match": {'context': concated_test_contexts}}})

                    hit = res['hits']['hits'][0]
                    hit_entity = hit['_source']['entity']

                    hit_entities.append(hit_entity)

                    entity_triples = {(head, tail, tag) for head, tail, tag in self.triples
                                      if head == hit_entity or tail == hit_entity}

                    for entity_triple in entity_triples:
                        head, tail, tag = entity_triple
                        if head == hit_entity:
                            head = entity
                        if tail == hit_entity:
                            tail = entity
                        mod_triple = (head, tail, tag)
                        mod_triples.add(mod_triple)

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
