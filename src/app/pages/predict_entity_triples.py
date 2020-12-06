import os
import random
import re
from typing import Set

import pandas as pd
import streamlit as st
from elasticsearch import Elasticsearch

from app.util import load_dataset
from eval.custom_evaluator import CustomEvaluator
from models.baseline_model import BaselineModel


def render_predict_entity_triples_page():

    #
    # Sidebar: Input model independent params
    #

    st.sidebar.markdown('---')

    model_selection = st.sidebar.selectbox('Model', ['Baseline'])
    dataset_dir = st.sidebar.text_input('Dataset directory', 'data/oke.fb15k237_30061990_50')
    random_seed = st.sidebar.number_input('Random seed', value=0)

    st.sidebar.markdown('PYTHONHASHSEED = %s' % os.getenv('PYTHONHASHSEED'))

    #
    # Sidebar: Input model dependent params
    #

    st.sidebar.markdown('---')

    if model_selection == 'Baseline':
        es_host = st.sidebar.text_input('Elasticsearch Host', value='localhost:9200')
        es_index = st.sidebar.text_input('Elasticsearch Index Name', value='cw-contexts-v7-enwiki-20200920-100-500')
        ow_db = st.sidebar.text_input('Open-World DB', value='data/ow-contexts-v7-enwiki-20200920-100-500.db')

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

    st.title('Predict entity triples')

    prefix = st.text_input('Entity prefix', value='Ab')

    options = ['%s (%d)' % (id2ent[entity], entity) for entity in ow_entities]
    filtered_ent_names = [opt for opt in options if opt.startswith(prefix)]
    filtered_ent_names.sort()

    selected_option = st.selectbox('Entity (ID)', filtered_ent_names)
    regex = r'^.+ \((\d+)\)$'  # any string followed by space and number in parentheses, e.g. "Foo bar (123)"
    selected_entity = int(re.match(regex, selected_option).group(1))  # get number, e.g. 123

    #
    # Create model & Predict
    #

    if model_selection == 'Baseline':
        es = Elasticsearch([es_host])
        model = BaselineModel(dataset_dir, es, es_index, ow_db)
        model.calc_score_matrix(ow_entities)

        pred_triples = model.predict(selected_entity)

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

    df = pd.DataFrame(pred_triples, columns=['Head', 'Relation', 'Tail'])
    # df = df.style.applymap(highlight)
    st.dataframe(df)
