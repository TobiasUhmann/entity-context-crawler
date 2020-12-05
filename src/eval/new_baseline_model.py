import pickle
import sqlite3
from collections import Counter
from datetime import datetime
from typing import List, Tuple, Set, Optional

import numpy as np
import sparse
import torch
from elasticsearch import Elasticsearch
from pykeen.models import Model
from pykeen.triples import TriplesFactory
from ryn.graphs.split import Dataset
from ryn.kgc.data import load_datasets
from tqdm import tqdm

from dao.contexts_db import select_contexts
from util.custom_types import Entity, Triple


class BaselineModel(Model):
    def __init__(self, dataset: Dataset, es: Elasticsearch, es_index: str, ow_contexts_db: str):
        """
        :param es: ES index containing closed world contexts
        :param ow_contexts_db: DB containing open world contexts
        """

        _, keen_dataset = load_datasets(path='data/oke.fb15k237_26041992_50')

        train_triples: np.ndarray = keen_dataset.training.triples
        valid_triples: np.ndarray = keen_dataset.validation.triples
        test_triples: np.ndarray = keen_dataset.testing.triples

        all_triples = np.concatenate((train_triples, valid_triples, test_triples))

        super().__init__(triples_factory=TriplesFactory(triples=all_triples))

        self.es = es
        self.es_index = es_index
        self.query_contexts_db = ow_contexts_db
        self.id2ent = dataset.id2ent
        self.id2rel = dataset.id2rel

        cw_triples = dataset.cw_train.triples | dataset.cw_valid.triples
        self.train_triples = list(cw_triples)
        ow_triples: Set = dataset.ow_valid.triples
        self.gt_triples = list(cw_triples | ow_triples)

        #
        # Rank triples by (<head importance> + <tail importance>)
        #

        self.head_counter = Counter([head for head, _, _ in self.gt_triples])
        self.tail_counter = Counter([tail for _, tail, _ in self.gt_triples])

        self.gt_triples.sort(key=lambda t: self.score(t), reverse=True)

        self.score_matrix = None

    def score(self, triple):
        return self.head_counter[triple[0]] + self.tail_counter[triple[0]]

    def calc_score_matrix(self, ow_ent_batch: List[Entity]):
        # ent_count = len(self.id2ent)
        # rel_count = len(self.id2rel)
        # score_matrix = sparse.DOK((ent_count, rel_count, ent_count))
        #
        # for ow_ent in tqdm(ow_ent_batch):
        #     pred_ow_triples_batch, pred_cw_ent_batch = self.predict([ow_ent])
        #     pred_ow_triples, pred_cw_ent = pred_ow_triples_batch[0], pred_cw_ent_batch[0]
        #
        #     if pred_cw_ent:
        #         for h, t, r in pred_ow_triples:
        #             score_matrix[h, r, t] += self.score((h, r, t))
        #
        # self.score_matrix = score_matrix.to_coo()

        with open('data/score_matrix.p', 'rb') as fh:
            self.score_matrix = pickle.load(fh).to_coo()

    def predict(self, query_entity_batch: List[Entity]) \
            -> Tuple[List[List[Triple]], List[Optional[Entity]]]:
        """
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
                query_entity_contexts = [c.masked_context for c in select_contexts(query_contexts_conn, query_entity)]
                query_entity_contexts = [context.replace('#', '') for context in query_entity_contexts]

                # random.shuffle(query_entity_contexts)

                if not query_entity_contexts:
                    # log('{} | {} -> <NONE>'.format(count, query_entity_name))
                    hit_entity_batch.append(None)
                    pred_triples_batch.append(None)

                else:
                    concated_query_entity_contexts = ' '.join(query_entity_contexts)[:1024]
                    es_result = self.es.search(index=self.es_index,
                                               body={'query': {'match': {'context': concated_query_entity_contexts}}})

                    es_hits = es_result['hits']['hits']
                    for es_hit in es_hits[:1]:
                        hit_entity = es_hit['_source']['entity']

                        # log('{} | {} -> {}'.format(count, query_entity_name, self.id2ent[hit_entity]))

                        hit_entity_triples = [(head, tail, rel) for head, tail, rel in self.gt_triples
                                              if head == hit_entity or tail == hit_entity]

                        pred_triples = [(query_entity if head == hit_entity else head,
                                         query_entity if tail == hit_entity else tail,
                                         rel)
                                        for head, tail, rel in hit_entity_triples]

                        hit_entity_batch.append(hit_entity)
                        pred_triples_batch.append(pred_triples)

        return pred_triples_batch, hit_entity_batch

    def predict_scores_all_heads(
            self,
            rt_batch: torch.LongTensor,
            slice_size: Optional[int] = None,
    ) -> torch.FloatTensor:

        result = torch.empty((len(rt_batch), len(self.id2ent)))

        print(rt_batch)
        for i, rt in enumerate(rt_batch):
            r, t = rt.tolist()
            sparse_scores = self.score_matrix[:, r, t]
            result[i, :] = torch.tensor(sparse_scores.todense())

        return result


    def predict_scores_all_tails(
            self,
            hr_batch: torch.LongTensor,
            slice_size: Optional[int] = None,
    ) -> torch.FloatTensor:

        result = []

        for h, r in hr_batch:
            head, rel = h.item(), r.item()

            pred_ow_triples_batch, pred_cw_ent_batch = self.predict([head])
            pred_ow_triples, pred_cw_ent = pred_ow_triples_batch[0], pred_cw_ent_batch[0]

            all_tail_scores = [-1] * len(self.id2ent)

            if pred_cw_ent is not None:
                filtered_pred_triples = [pred_ow_triple for pred_ow_triple in pred_ow_triples
                                         if pred_ow_triple[1] == rel]

                for filtered_pred_triple in filtered_pred_triples:
                    all_tail_scores[filtered_pred_triple[2]] = self.score(filtered_pred_triple)

            result.append(all_tail_scores)

        return torch.tensor(result, dtype=torch.float)


def log(msg: str):
    print('{} | {}'.format(datetime.now().strftime("%H:%M:%S"), msg))
