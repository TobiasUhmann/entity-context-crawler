import streamlit as st

from app.pages.evaluate_model import render_evaluate_model_page
from app.pages.model_overview import render_model_overview_page
from app.pages.predict_entity_triples import render_predict_entity_triples_page
from app.pages.show_entity_contexts import render_show_entity_contexts_page
from app.pages.show_entity_triples import render_show_entity_triples_page
from app.pages.show_relation_triples import render_show_relation_triples_page


def render_index():
    """ Render the part that is common to all pages: The sidebar navigation """

    navigate_to = st.sidebar.radio('', [
        'Model Overview',
        'Show entity contexts',
        'Show entity triples',
        'Show relation triples',
        'Predict entity triples',
        'Evaluate model'
    ])

    if navigate_to == 'Model Overview':
        render_model_overview_page()
    elif navigate_to == 'Show entity contexts':
        render_show_entity_contexts_page()
    elif navigate_to == 'Show entity triples':
        render_show_entity_triples_page()
    elif navigate_to == 'Show relation triples':
        render_show_relation_triples_page()
    elif navigate_to == 'Predict entity triples':
        render_predict_entity_triples_page()
    elif navigate_to == 'Evaluate model':
        render_evaluate_model_page()
