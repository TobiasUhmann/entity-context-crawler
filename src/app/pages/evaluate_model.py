import os
import random
from typing import Set

import streamlit as st
import torch
from elasticsearch import Elasticsearch
from pykeen.evaluation import RankBasedEvaluator, RankBasedMetricResults

from app.common import load_dataset
from eval.custom_evaluator import CustomEvaluator, TotalResult
from models.baseline_model import BaselineModel


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

    ow_entities: Set[int] = dataset.ow_valid.owe
    ow_triples = [(head, rel, tail) for head, tail, rel in dataset.ow_valid.triples]

    #
    # Model independent params
    #

    st.sidebar.markdown('---')

    dataset_dir = st.sidebar.text_input('Dataset', 'data/oke.fb15k237_30061990_50')

    model_selection = st.sidebar.selectbox('Model', ['Baseline 10', 'Baseline 100'])

    ow_contexts_db = st.sidebar.text_input('OW Contexts DB', value='data/ow-contexts-v7-enwiki-20200920-100-500.db')

    random_seed = st.sidebar.number_input('Random seed', value=0)
    random.seed(random_seed)

    st.sidebar.markdown('PYTHONHASHSEED = %s' % os.getenv('PYTHONHASHSEED'))

    eval_mode = st.sidebar.selectbox('Eval Mode', ['Custom', 'Pykeen'], index=1)

    #
    # Model dependent params
    #

    st.sidebar.markdown('---')

    if model_selection == 'Baseline 10':
        es_url = st.sidebar.text_input('Elasticsearch URL', value='localhost:9200')
        es = Elasticsearch([es_url])
        cw_es_index = st.sidebar.text_input('CW Elasticsearch Index', value='cw-contexts-v7-enwiki-20200920-10-500')
        model = BaselineModel(dataset_dir, es, cw_es_index, ow_contexts_db)

    elif model_selection == 'Baseline 100':
        es_url = st.sidebar.text_input('Elasticsearch URL', value='localhost:9200')
        es = Elasticsearch([es_url])
        cw_es_index = st.sidebar.text_input('CW Elasticsearch Index', value='cw-contexts-v7-enwiki-20200920-100-500')
        model = BaselineModel(dataset_dir, es, cw_es_index, ow_contexts_db)

    else:
        raise AssertionError()

    #
    # Evaluate model
    #

    st.title('Evaluate model')

    shuffled_ow_entities = list(ow_entities)
    random.shuffle(shuffled_ow_entities)

    if eval_mode == 'Custom':
        evaluator = CustomEvaluator(model, ow_triples, ow_entities)
        result: TotalResult = evaluator.run()

        print(result.map)

    elif eval_mode == 'Pykeen':
        evaluator = RankBasedEvaluator()
        ow_triples_tensor: torch.LongTensor = torch.tensor(ow_triples, dtype=torch.long)
        result: RankBasedMetricResults = evaluator.evaluate(model, ow_triples_tensor, batch_size=1024)

        print(result)
