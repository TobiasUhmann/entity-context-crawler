import os
import random
from typing import Set

import streamlit as st
import torch
from elasticsearch import Elasticsearch
from pykeen.evaluation import RankBasedEvaluator, RankBasedMetricResults
from torch import LongTensor, tensor

from app.util import load_dataset
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

    # total_result = Evaluator(model, ow_triples, shuffled_ow_entities).run()

    evaluator = RankBasedEvaluator()
    mapped_triples: LongTensor = tensor(ow_triples, dtype=torch.long)
    total_result: RankBasedMetricResults = evaluator.evaluate(model, mapped_triples, batch_size=1024)

    print(total_result)

    #
    # Show results
    #

    # results, mean_ap = total_result.results, total_result.map
    #
    # data = [(id2ent[ow_entity], result.precision, result.recall, result.f1, result.ap)
    #         for ow_entity, result in zip(shuffled_ow_entities, results)]
    # data_frame = pd.DataFrame(data, columns=['Entity', 'Precision', 'Recall', 'F1', 'AP'])
    # st.dataframe(data_frame)
    #
    # st.write('mAP = {:.4f}'.format(mean_ap))
