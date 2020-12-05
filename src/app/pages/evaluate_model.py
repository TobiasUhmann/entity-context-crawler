import os
import pandas as pd
import random
import streamlit as st

from elasticsearch import Elasticsearch
from typing import Set

from app.util import load_dataset
from eval.old_baseline_model import BaselineModel
from eval.evaluator import Evaluator
from util.custom_types import Entity, Triple


def render_evaluate_model_page():
    """
    - Load dataset
    - Render sidebar
        - Random seed selection & Show PYTHONHASHSEED
        - Limit entities selection
        - Model selection & Model specific config
            - Baseline 10: ES URL
            - Baseline 100: ES URL
    - Render main content
        - Evaluate model
        - Show results
    """

    dataset = load_dataset()

    id2ent = dataset.id2ent

    ow_entities: Set[Entity] = dataset.ow_valid.owe
    ow_triples: Set[Triple] = dataset.ow_valid.triples

    #
    # Model independent params
    #

    st.sidebar.markdown('---')

    model_selection = st.sidebar.selectbox('Model', ['Baseline 10', 'Baseline 100'])

    ow_contexts_db = st.sidebar.text_input('OW Contexts DB', value='data/ow-contexts-v7-enwiki-20200920-100-500.db')

    limit_entities = st.sidebar.number_input('Limit entities', value=10)

    random_seed = st.sidebar.number_input('Random seed', value=0)
    random.seed(random_seed)

    st.sidebar.markdown('PYTHONHASHSEED = %s' % os.getenv('PYTHONHASHSEED'))

    #
    # Model dependent params
    #

    st.sidebar.markdown('---')

    if model_selection == 'Baseline 10':
        es_url = st.sidebar.text_input('Elasticsearch URL', value='localhost:9200')
        es = Elasticsearch([es_url])
        cw_es_index = st.sidebar.text_input('CW Elasticsearch Index', value='cw-contexts-v7-enwiki-20200920-10-500')
        model = BaselineModel(dataset, es, cw_es_index, ow_contexts_db)

    elif model_selection == 'Baseline 100':
        es_url = st.sidebar.text_input('Elasticsearch URL', value='localhost:9200')
        es = Elasticsearch([es_url])
        cw_es_index = st.sidebar.text_input('CW Elasticsearch Index', value='cw-contexts-v7-enwiki-20200920-100-500')
        model = BaselineModel(dataset, es, cw_es_index, ow_contexts_db)

    else:
        raise AssertionError()

    #
    # Evaluate model
    #

    st.title('Evaluate model')

    if limit_entities:
        shuffled_ow_entities = random.sample(ow_entities, limit_entities)
    else:
        shuffled_ow_entities = list(ow_entities)
        random.shuffle(shuffled_ow_entities)

    total_result = Evaluator(model, ow_triples, shuffled_ow_entities).run()

    #
    # Show results
    #

    results, mean_ap = total_result.results, total_result.map

    data = [(id2ent[ow_entity], result.precision, result.recall, result.f1, result.ap)
            for ow_entity, result in zip(shuffled_ow_entities, results)]
    data_frame = pd.DataFrame(data, columns=['Entity', 'Precision', 'Recall', 'F1', 'AP'])
    st.dataframe(data_frame)

    st.write('mAP = {:.4f}'.format(mean_ap))
