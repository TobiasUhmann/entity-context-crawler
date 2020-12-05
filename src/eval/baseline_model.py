import logging
import sqlite3
import sys
from collections import Counter
from typing import List, Set, Optional, Dict

import numpy as np
import sparse
import torch
from elasticsearch import Elasticsearch
from pykeen.models import Model
from pykeen.triples import TriplesFactory
from ryn.graphs import split
from ryn.kgc import keen
from ryn.kgc.data import load_datasets
from torch import FloatTensor, LongTensor, tensor
from tqdm import tqdm

from dao.contexts_db import select_contexts
from util.custom_types import Entity, Triple


class BaselineModel(Model):
    """ Partial implementation of :class:`pykeen.Model` (so that Pykeen evaluation works) """

    def __init__(self, dataset_dir: str, es: Elasticsearch, es_index: str, ow_contexts_db: str):

        #
        # Init super class with TriplesFactory used for target filtering during evaluation
        #

        split_dataset: split.Dataset
        keen_dataset: keen.Dataset
        split_dataset, keen_dataset = load_datasets(path=dataset_dir)

        cw_train_1_text_triples: np.ndarray = keen_dataset.training.triples
        cw_train_2_text_triples: np.ndarray = keen_dataset.validation.triples
        cw_valid_text_triples: np.ndarray = keen_dataset.testing.triples

        cw_text_triples = np.concatenate((cw_train_1_text_triples, cw_train_2_text_triples, cw_valid_text_triples))

        super().__init__(triples_factory=TriplesFactory(triples=cw_text_triples))

        #
        # Save params and dataset elements for later usage
        #

        self.es: Elasticsearch = es
        self.es_index: str = es_index
        self.ow_contexts_db: str = ow_contexts_db

        self.id2ent: Dict[int, str] = split_dataset.id2ent
        self.id2rel: Dict[int, str] = split_dataset.id2rel

        cw_triples: Set[Triple] = split_dataset.cw_train.triples | split_dataset.cw_valid.triples
        self.cw_triples: List[Triple] = [(head, rel, tail) for head, tail, rel in cw_triples]

        ow_triples: Set[Triple] = split_dataset.ow_valid.triples
        self.cw_ow_triples: List[Triple] = [(head, rel, tail) for head, tail, rel in cw_triples | ow_triples]

        self.score_matrix = None

        #
        # Score head/tail entities by frequency
        #

        self.head_counter = Counter([head for head, _, _ in self.cw_ow_triples])
        self.tail_counter = Counter([tail for _, _, tail in self.cw_ow_triples])

    def predict(self, ow_ent: Entity) -> Optional[List[Triple]]:
        """
        Prediction for an OW entity:

        - Get context for OW entity from OW contexts DB
        - Query ES index for most similar CW entity context
        - Get CW entity's triples and replace the respective CW heads/tails with OW entity
        - Return modified CW triples as predicted OW triples

        :return: Predicted OW triples, or 'None' if no contexts exist for the OW entity
        """

        #
        # SELECT OW contexts from DB, remove masks ('###'), and concatenate them
        #

        with sqlite3.connect(self.ow_contexts_db) as query_contexts_conn:
            ow_db_contexts = select_contexts(query_contexts_conn, ow_ent)

        masked_ow_contexts = [db_context.masked_context for db_context in ow_db_contexts]
        blanked_ow_contexts = [context.replace('#', '') for context in masked_ow_contexts]

        if not blanked_ow_contexts:
            return None

        ow_context = ' '.join(blanked_ow_contexts)

        #
        # Query ES for most similiar CW entity
        #

        # ES allows for max. 1024 chars
        es_result = self.es.search(index=self.es_index,
                                   body={'query': {'match': {'context': ow_context[:1024]}}})

        es_hit = es_result['hits']['hits'][0]  # Only consider top 1 hit

        cw_ent = es_hit['_source']['entity']
        logging.info('OW "{}" -> CW "{}"'.format(self.id2ent[ow_ent], self.id2ent[cw_ent]).encode('utf-8'))

        #
        # Get CW triples, modify them (replace CW entity with OW entity)
        #

        cw_triples = [(head, rel, tail) for head, rel, tail in self.cw_ow_triples
                      if head == cw_ent or tail == cw_ent]

        pred_triples = [(ow_ent if head == cw_ent else head,
                         rel,
                         ow_ent if tail == cw_ent else tail)
                        for head, rel, tail in cw_triples]

        return pred_triples

    def score(self, triple):
        return self.head_counter[triple[0]] + self.tail_counter[triple[2]]

    def calc_score_matrix(self, ow_ent_batch: List[Entity]):

        # Create sparse DOK matrix (which is suitable for counting) containing all triple scores
        ent_count = len(self.id2ent)
        rel_count = len(self.id2rel)
        score_matrix = sparse.DOK((ent_count, rel_count, ent_count))

        # For each OW entity: Predict and score all triples, and increase respective score in matrix
        for ow_ent in tqdm(ow_ent_batch):
            pred_ow_triples = self.predict(ow_ent)

            if pred_ow_triples:
                for head, rel, tail in pred_ow_triples:
                    score_matrix[head, rel, tail] += self.score((head, rel, tail))

        # Save sparse matrix in COO format (for later slicing)
        self.score_matrix = score_matrix.to_coo()

    def predict_scores_all_heads(self, rt_batch: LongTensor, slice_size: Optional[int] = None) \
            -> FloatTensor:
        """
        Overrides :func:`pykeen.models.Model.predict_scores_all_heads`

        :param slice_size: Ignored
        """

        result: FloatTensor = torch.empty((len(rt_batch), len(self.id2ent)), dtype=FloatTensor)

        for i, rel_tail in enumerate(rt_batch):
            rel, tail = rel_tail.tolist()
            sparse_scores = self.score_matrix[:, rel, tail]
            result[i, :] = tensor(sparse_scores.todense())

        return result

    def predict_scores_all_tails(self, hr_batch: LongTensor, slice_size: Optional[int] = None) \
            -> FloatTensor:
        """
        Overrides :func:`pykeen.models.Model.predict_scores_all_tails`

        :param slice_size: Ignored
        """

        result: FloatTensor = torch.empty((len(hr_batch), len(self.id2ent)), dtype=FloatTensor)

        for i, head_rel in enumerate(hr_batch):
            head, rel = head_rel.tolist()
            sparse_scores = self.score_matrix[head, rel, :]
            result[i, :] = tensor(sparse_scores.todense())

        return result
