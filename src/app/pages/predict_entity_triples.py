import os
import random
import re
from typing import Set

import pandas as pd
import streamlit as st
from elasticsearch import Elasticsearch

from app.util import load_dataset
from eval.old_baseline_model import BaselineModel
from eval.my_evaluator import MyEvaluator


def render_predict_entity_triples_page():
    """
    - Load dataset
    - Render sidebar
        - Model independent params
        - Model dependent params
    - Render main content
        - Entity prefix input & Entity name selection
        - Evaluate model
        - Show predicted triples
    """

    dataset = load_dataset()

    id2ent = dataset.id2ent
    id2rel = dataset.id2rel

    ow_entities: Set[int] = dataset.ow_valid.owe
    ow_triples: Set = dataset.ow_valid.triples

    #
    # Sidebar: Model independent params
    #

    st.sidebar.markdown('---')

    model_selection = st.sidebar.selectbox('Model', ['Baseline 10', 'Baseline 100'])

    ow_contexts_db = st.sidebar.text_input('OW Contexts DB', value='data/ow-contexts-v7-enwiki-20200920-100-500.db')

    random_seed = st.sidebar.number_input('Random seed', value=0)
    random.seed(random_seed)

    st.sidebar.markdown('PYTHONHASHSEED = %s' % os.getenv('PYTHONHASHSEED'))

    #
    # Sidebar: Model dependent params
    #

    st.sidebar.markdown('---')

    if model_selection == 'Baseline 10':
        es_url = st.sidebar.text_input('Elasticsearch Host', value='localhost:9200')
        es = Elasticsearch([es_url])
        cw_es_index = st.sidebar.text_input('CW Elasticsearch Index', value='cw-contexts-v7-enwiki-20200920-10-500')
        model = BaselineModel(dataset, es, cw_es_index, ow_contexts_db)

    elif model_selection == 'Baseline 100':
        es_url = st.sidebar.text_input('Elasticsearch Host', value='localhost:9200')
        es = Elasticsearch([es_url])
        cw_es_index = st.sidebar.text_input('CW Elasticsearch Index', value='cw-contexts-v7-enwiki-20200920-100-500')
        model = BaselineModel(dataset, es, cw_es_index, ow_contexts_db)

    else:
        raise AssertionError()

    #
    # Entity prefix input & Entity name selection
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
    # Evaluate model
    #

    st.markdown('---')

    evaluator = MyEvaluator(model, ow_triples, [selected_entity])
    total_result = evaluator.run()
    result = total_result.results[0]

    output = '\n'
    output += '{:20} {:.2f}'.format('Precision', result.precision) + '\n'
    output += '{:20} {:.2f}'.format('Recall', result.recall) + '\n'
    output += '{:20} {:.2f}'.format('F1-Score', result.f1) + '\n'
    output += '{:20} {:.2f}'.format('Average Precision', result.ap) + '\n'
    st.markdown('```' + output + '```')

    pred_triples = result.pred_ow_triples
    pred_triples_hits = result.pred_ow_triples_hits

    def highlight(hit):
        if hit == '+':
            return 'color: white; background-color: green'
        elif hit == '-':
            return 'color: white; background-color: red'
        else:
            return 'color: black; background-color: white'

    data = [(hit, id2ent[t[0]], id2ent[t[1]], id2rel[t[2]])
            for t, hit in zip(pred_triples, pred_triples_hits)]
    df = pd.DataFrame(data, columns=['', 'Head', 'Tail', 'Rel'])
    df = df.style.applymap(highlight)
    st.dataframe(df)


def truncate(text, max_len):
    return (text[:max_len - 3] + '...') if len(text) > max_len else text
