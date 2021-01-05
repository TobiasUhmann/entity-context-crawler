import os
import pickle
import random
import re
from typing import List

import pandas as pd
import streamlit as st
import torch
from elasticsearch import Elasticsearch

from app.common import load_dataset
from models.baseline_model import BaselineModel
from util.types import Triple


def render_rank_triple_page():
    #
    # Sidebar: Input model independent params
    #

    st.sidebar.header('Model independent params')

    model_selection = st.sidebar.selectbox('Model', ['Baseline'])
    dataset_dir = st.sidebar.text_input('Dataset directory', 'data/oke.fb15k237_30061990_50')
    random_seed = st.sidebar.number_input('Random seed', value=0)

    st.sidebar.markdown('PYTHONHASHSEED = %s' % os.getenv('PYTHONHASHSEED'))

    #
    # Sidebar: Input model dependent params
    #

    st.sidebar.header('Model dependent params')

    if model_selection == 'Baseline':
        baseline_es_host = st.sidebar.text_input('Elasticsearch Host', value='localhost:9200')
        baseline_es_index = st.sidebar.text_input('Elasticsearch Index Name',
                                                  value='cw-contexts-v7-2020-12-31')
        baseline_ow_db = st.sidebar.text_input('Open-World DB', value='data/ow-contexts-v7-2020-12-31.db')
        baseline_pickle_file = st.sidebar.text_input('Pickle File', value='data/baseline-v1-enwiki-20200920-100-500.p')

    else:
        raise AssertionError()

    #
    # Load dataset & Seed random
    #

    dataset = load_dataset(dataset_dir)

    id2ent = dataset.id2ent
    id2rel = dataset.id2rel

    ow_entities = list(dataset.ow_valid.owe)
    ow_triples = [(head, rel, tail) for head, tail, rel in dataset.ow_valid.triples]

    random.seed(random_seed)

    #
    # Main: Title & Input entity
    #

    st.title('Rank triple')

    head = st.number_input('Head', value=1)
    rel = st.number_input('Relation', value=1)
    tail = st.number_input('Tail', value=1)

    #
    # Create model & Predict
    #

    if model_selection == 'Baseline':
        es = Elasticsearch([baseline_es_host])
        model = BaselineModel(dataset_dir, es, baseline_es_index, baseline_ow_db)

        with open(baseline_pickle_file, 'rb') as fh:
            model.score_matrix = pickle.load(fh)

        head_scores = model.predict_scores_all_heads(torch.tensor([[rel, tail]], dtype=torch.long))
        head_triples = [(h, rel, tail) for h in head_scores.numpy().nonzero()[1].tolist()]

        tail_scores = model.predict_scores_all_tails(torch.tensor([[head, rel]], dtype=torch.long))
        tail_triples = [(head, rel, t) for t in tail_scores.numpy().nonzero()[1].tolist()]

        pred_triples = list(set(head_triples) | set(tail_triples))

    else:
        raise AssertionError()

    #
    # Main: Output predicted triples
    #

    st.markdown('---')

    # def highlight(hit):
    #     if hit == '+':
    #         return 'color: white; background-color: green'
    #     elif hit == '-':
    #         return 'color: white; background-color: red'
    #     else:
    #         return 'color: black; background-color: white'

    def background_color(row):
        if row.Truth == 'TP':
            return ['background-color: #66bb6a'] * len(row)
        elif row.Truth == 'FP':
            return ['background-color: #ff7043'] * len(row)
        elif row.Truth == 'FN':
            return ['background-color: #ffee58'] * len(row)

    actual_triples = [(head, rel, tail)]
    pred_and_actual_triples = list(set(pred_triples) | set(actual_triples))

    def truth(triple: Triple):
        if triple in pred_triples and triple in actual_triples:
            return 'TP'
        elif triple in pred_triples and triple not in actual_triples:
            return 'FP'
        elif triple not in pred_triples and triple in actual_triples:
            return 'FN'
        elif triple not in pred_triples and triple not in actual_triples:
            return 'TN'
        else:
            raise AssertionError()

    data = [(id2ent[head], id2rel[rel], id2ent[tail], model.score((head, rel, tail)), truth((head, rel, tail)))
            for head, rel, tail in pred_and_actual_triples]

    sorted_data = sorted(data, key=lambda tup: tup[3], reverse=True)

    df = pd.DataFrame(sorted_data, columns=['Head', 'Relation', 'Tail', 'Score', 'Truth'])
    df = df.style.apply(background_color, axis=1)
    st.dataframe(df)
