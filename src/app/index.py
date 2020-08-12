import streamlit as st

from app.pages.build_es_index import render_build_es_index_page
from app.pages.evaluate_model import render_evaluate_model_page
from app.pages.predict_entity_triples import render_predict_entity_triples_page
from app.pages.show_entity_triples import render_show_entity_triples_page
from app.pages.show_relation_triples import render_show_relation_triples_page


def render_index():
    #
    # Sidebar
    #

    navigate_to = st.sidebar.radio('', [
        'Build ES index',
        'Show entity triples',
        'Show relation triples',
        'Predict entity triples',
        'Evaluate model'
    ])

    if navigate_to == 'Build ES index':
        render_build_es_index_page()
    elif navigate_to == 'Show entity triples':
        render_show_entity_triples_page()
    elif navigate_to == 'Show relation triples':
        render_show_relation_triples_page()
    elif navigate_to == 'Predict entity triples':
        render_predict_entity_triples_page()
    elif navigate_to == 'Evaluate model':
        render_evaluate_model_page()
