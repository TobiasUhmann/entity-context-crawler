import os
import random
import streamlit as st

from elasticsearch import Elasticsearch

from app.util import load_dataset
from eval.baseline_model import BaselineModel
from eval.evaluator import Evaluator


def render_evaluate_model_page():
    dataset = load_dataset()

    id2ent = dataset.id2ent
    id2rel = dataset.id2rel

    cw_triples = {(id2ent[head], id2ent[tail], id2rel[rel])
                  for head, tail, rel in dataset.cw_train.triples | dataset.cw_valid.triples}

    ow_entities = {id2ent[ent] for ent in dataset.ow_valid.owe}
    ow_triples = {(id2ent[head], id2ent[tail], id2rel[rel])
                  for head, tail, rel in dataset.ow_valid.triples}

    all_triples = list(cw_triples | ow_triples)

    #
    # Sidebar
    #

    st.sidebar.markdown('---')

    random_seed = st.sidebar.number_input('Random seed', value=0, format='%d')
    random.seed(random_seed)

    st.sidebar.markdown('PYTHONHASHSEED = %s' % os.getenv('PYTHONHASHSEED'))

    #
    # Sidebar: Model selection
    #

    model_selection = st.sidebar.selectbox('Model', ['Baseline'])

    if model_selection == 'Baseline':
        es_url = st.sidebar.text_input('Elasticsearch', value='localhost:9200')
        es = Elasticsearch([es_url])
        es_index = 'enwiki-latest-cw-contexts-100-500'
        ow_contexts_db = 'data/enwiki-latest-ow-contexts-100-500.db'
        ent2id = {ent: id for id, ent in id2ent.items()}
        model = BaselineModel(es, es_index, ow_contexts_db, id2ent, ent2id, set(all_triples))

    #
    # Evaluate model
    #

    st.title('Evaluate model')

    some_ow_entities = random.sample(ow_entities, 10)
    evaluator = Evaluator(model, ow_triples, some_ow_entities)
    total_result = evaluator.run()
    result, mAP = total_result.results[0], total_result.map

    output = '\n'
    output += '{:20} {:.2f}'.format('Precision', result.precision) + '\n'
    output += '{:20} {:.2f}'.format('Recall', result.recall) + '\n'
    output += '{:20} {:.2f}'.format('F1-Score', result.f1) + '\n'
    output += '{:20} {:.2f}'.format('Average Precision', result.ap) + '\n'
    st.markdown('```' + output + '```')

    st.write()
    st.write('mAP = ', mAP)
