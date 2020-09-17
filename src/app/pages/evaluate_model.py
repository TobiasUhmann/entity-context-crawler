import os
import random
import streamlit as st

from elasticsearch import Elasticsearch
from ryn.graphs.split import Dataset
from typing import Set

from app.util import load_dataset
from eval.baseline_model import BaselineModel
from eval.evaluator import Evaluator
from custom_types import Entity, Triple


def render_evaluate_model_page():
    """
    - Load dataset
    - Render sidebar
        - Random seed selection & Show PYTHONHASHSEED
        - Model selection
    - Render main content
        - Evaluate model
        - Show mAP
    """

    dataset = load_dataset()

    id2ent = dataset.id2ent

    ow_entities: Set[Entity] = dataset.ow_valid.owe
    ow_triples: Set[Triple] = dataset.ow_valid.triples

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

    model_selection = st.sidebar.selectbox('Model', ['Baseline 10', 'Baseline 100'])

    if model_selection == 'Baseline 10':
        es_url = st.sidebar.text_input('Elasticsearch URL', value='localhost:9200')
        es = Elasticsearch([es_url])
        es_index = 'enwiki-latest-cw-contexts-10-500'
        ow_contexts_db = 'data/enwiki-latest-ow-contexts-10-500.db'
        model = BaselineModel(dataset, es, es_index, ow_contexts_db)

    elif model_selection == 'Baseline 100':
        es_url = st.sidebar.text_input('Elasticsearch URL', value='localhost:9200')
        es = Elasticsearch([es_url])
        es_index = 'enwiki-latest-cw-contexts-100-500'
        ow_contexts_db = 'data/enwiki-latest-ow-contexts-100-500.db'
        model = BaselineModel(dataset, es, es_index, ow_contexts_db)

    #
    # Evaluate model
    #

    st.title('Evaluate model')

    some_ow_entities = random.sample(ow_entities, 10)
    evaluator = Evaluator(model, ow_triples, some_ow_entities)
    total_result = evaluator.run()
    results, mAP = total_result.results, total_result.map

    for result, ow_entity in zip(results, some_ow_entities):
        output = '\n'
        output += '%s' % id2ent[ow_entity] + '\n'
        output += '{:20} {:.2f}'.format('Precision', result.precision) + '\n'
        output += '{:20} {:.2f}'.format('Recall', result.recall) + '\n'
        output += '{:20} {:.2f}'.format('F1-Score', result.f1) + '\n'
        output += '{:20} {:.2f}'.format('Average Precision', result.ap) + '\n'
        st.markdown('```' + output + '```')

    st.write()
    st.write('mAP = ', mAP)
