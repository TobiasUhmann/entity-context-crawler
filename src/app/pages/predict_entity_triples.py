import os
import pandas as pd
import random
import re
import streamlit as st

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

    if model_selection == 'Baseline 10':
        es_url = st.sidebar.text_input('Elasticsearch URL', value='localhost:9200')
        es = Elasticsearch([es_url])
        es_index = 'enwiki-latest-cw-contexts-10-500'
        ow_contexts_db = 'data/enwiki-latest-ow-contexts-10-500.db'
        ent2id = {ent: id for id, ent in id2ent.items()}
        model = BaselineModel(es, es_index, ow_contexts_db, id2ent, ent2id, all_triples)

    elif model_selection == 'Baseline 100':
        es_url = st.sidebar.text_input('Elasticsearch URL', value='localhost:9200')
        es = Elasticsearch([es_url])
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

    selected_option = st.selectbox('Entity (ID)', filtered_ent_names)
    regex = r'^.+ \((\d+)\)$'  # any string followed by space and number in parentheses, e.g. "Foo bar (123)"
    selected_entity = int(re.match(regex, selected_option).group(1))  # get number, e.g. 123

    #
    # Evaluate model
    #

    st.markdown('---')

    evaluator = Evaluator(model, ow_triples, [selected_entity])
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


def truncate(str, max_len):
    return (str[:max_len - 3] + '...') if len(str) > max_len else str
