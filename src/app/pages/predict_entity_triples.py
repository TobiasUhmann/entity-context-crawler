import os
import random
import re

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
    - Render sidebar
        - Random seed selection & Show PYTHONHASHSEED
        - Model selection
    - Render main content
        - Entity prefix input & Entity name selection
        - Evaluate model
        - Show predicted triples
    """

    dataset: Dataset = load_dataset()

    ow_entities: Set[int] = dataset.ow_valid.owe

    cw_triples: Set = dataset.cw_train.triples | dataset.cw_valid.triples
    ow_triples: Set = dataset.ow_valid.triples | dataset.ow_test.triples
    all_triples = cw_triples | ow_triples

    id2ent = dataset.id2ent
    id2rel = dataset.id2rel

    #
    # Sidebar: Random seed & PYTHONHASHSEED
    #

    st.sidebar.markdown('---')

    random_seed = st.sidebar.number_input('Random seed', value=0)
    random.seed(random_seed)

    st.sidebar.markdown('PYTHONHASHSEED = %s' % os.getenv('PYTHONHASHSEED'))

    #
    # Sidebar: Model selection
    #

    model_selection = st.sidebar.selectbox('Model', ['Baseline'])

    if model_selection == 'Baseline':
        es = Elasticsearch()
        es_index = 'enwiki-latest-cw-contexts-100-500'
        ow_contexts_db = 'data/enwiki-latest-ow-contexts-100-500.db'
        ent2id = {ent: id for id, ent in id2ent.items()}
        model = BaselineModel(es, es_index, ow_contexts_db, id2ent, ent2id, all_triples)

    #
    # Entity prefix input & Entity name selection
    #

    st.title('Predict entity triples')

    prefix = st.text_input('Entity prefix', value='Ab')

    options = ['%s (%d)' % (id2ent[entity], entity) for entity in ow_entities]
    filtered_ent_names = [opt for opt in options if opt.startswith(prefix)]
    filtered_ent_names.sort()

    selected_option = st.selectbox('Entity', filtered_ent_names)
    selected_entity = int(re.match(r'[\w\s]+ \((\d+)\)', selected_option).group(1))

    #
    # Render main content
    #

    some_ow_entities = [selected_entity]
    evaluator = Evaluator(model, ow_triples, some_ow_entities)

    with st.spinner('Evaluating model...'):
        total_result = evaluator.run()

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
                truncate(id2ent[head], 28),
                truncate(id2ent[tail], 28),
                id2rel[rel])
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
