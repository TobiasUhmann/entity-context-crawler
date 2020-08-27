import os
import random
import streamlit as st

from elasticsearch import Elasticsearch
from ryn.graphs.split import Dataset
from typing import Set

from app.util import load_dataset
from eval.baseline_model import BaselineModel
from eval.evaluator import Evaluator


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

    dataset: Dataset = load_dataset()

    ow_entities = dataset.ow_valid.owe

    cw_triples: Set = dataset.cw_train.triples | dataset.cw_valid.triples
    ow_triples: Set = dataset.ow_valid.triples
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
        es_url = st.sidebar.text_input('Elasticsearch URL', value='localhost:9200')
        es = Elasticsearch([es_url])
        es_index = 'enwiki-latest-cw-contexts-100-500'
        ow_contexts_db = 'data/enwiki-latest-ow-contexts-100-500.db'
        ent2id = {ent: id for id, ent in id2ent.items()}
        model = BaselineModel(es, es_index, ow_contexts_db, id2ent, ent2id, all_triples)

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
