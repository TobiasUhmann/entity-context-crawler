import os
import random
import streamlit as st

from collections import Counter
from elasticsearch import Elasticsearch
from ryn.graphs.split import Dataset
from typing import Set

from app.util import load_dataset
from eval.baseline_model import BaselineModel
from eval.evaluator import Evaluator


def render_predict_entity_triples_page():
    """
    - Load dataset
    - Render sidebar (model selectbox)
    - Render main content
    """

    dataset: Dataset = load_dataset()
    id2ent = dataset.id2ent
    ent2id = {ent: id for id, ent in id2ent.items()}
    id2rel = dataset.id2rel

    cw_triples: Set = dataset.cw_train.triples | dataset.cw_valid.triples
    ow_triples: Set = dataset.ow_valid.triples | dataset.ow_test.triples
    all_triples = list(cw_triples | ow_triples)

    ow_entities = dataset.ow_valid.owe

    #
    # Render sidebar
    #

    st.sidebar.markdown('---')

    random_seed = st.sidebar.number_input('Random seed', value=0, format='%d')
    random.seed(random_seed)

    st.sidebar.markdown('PYTHONHASHSEED = %s' % os.getenv('PYTHONHASHSEED'))

    model_selection = st.sidebar.selectbox('Model', ['Baseline'])
    if model_selection == 'Baseline':
        es = Elasticsearch()
        es_index = 'enwiki-latest-cw-contexts-100-500'
        ow_contexts_db = 'data/enwiki-latest-ow-contexts-100-500.db'
        model = BaselineModel(es, es_index, ow_contexts_db, id2ent, ent2id, all_triples)

    #
    # Render main content
    #

    head_counter = Counter([head for head, _, _ in all_triples])
    tail_counter = Counter([tail for _, tail, _ in all_triples])
    rel_counter = Counter([rel for _, _, rel in all_triples])

    all_triples.sort(key=lambda t: (head_counter[t[0]] + tail_counter[t[1]]) * rel_counter[t[2]], reverse=True)

    st.title('Predict entity triples')

    some_ow_entities = random.sample(ow_entities, 10)
    evaluator = Evaluator(model, ow_triples, some_ow_entities)

    with st.spinner('Evaluating model...'):
        total_result = evaluator.run()
    st.success('Model evaluated')

    results, mAP = total_result.results, total_result.map

    for ow_entity, result in zip(some_ow_entities, results):
        pred_ow_triples = result.pred_ow_triples
        precision = result.precision
        recall = result.recall
        f1 = result.f1
        ap = result.ap

        pred_cw_entity = result.pred_cw_entity
        pred_ow_triples_hits = result.pred_ow_triples_hits

        output = '\n'
        output += id2ent[ow_entity] + ' -> ' + (id2ent[pred_cw_entity] if pred_cw_entity is not None else '<None>') + '\n'
        output += 50 * '-' + '\n'

        count = 0
        for triple, hit in zip(pred_ow_triples, pred_ow_triples_hits):
            if count == 20:
                break
            head, tail, rel = triple
            hit_marker = '+' if hit else ' '
            output += '{} {:30} {:30} {}\n'.format(
                hit_marker,
                truncate('[{}] {}'.format(head_counter[head], id2ent[head]), 28),
                truncate('[{}] {}'.format(tail_counter[tail], id2ent[tail]), 28),
                '[{}] {}'.format(rel_counter[rel], id2rel[rel]))
            count += 1
        if len(pred_ow_triples) - count > 0:
            output += '[{} more hidden]'.format(len(pred_ow_triples) - count) + '\n'
        output += 50 * '-' + '\n'
        output += '{:20} {:.2f}'.format('Precision', precision) + '\n'
        output += '{:20} {:.2f}'.format('Recall', recall) + '\n'
        output += '{:20} {:.2f}'.format('F1-Score', f1) + '\n'
        output += '{:20} {:.2f}'.format('Average Precision', ap) + '\n'

        st.markdown('```' + output + '```')

    st.write()
    st.write('mAP = ', mAP)


def truncate(str, max_len):
    return (str[:max_len - 3] + '...') if len(str) > max_len else str
