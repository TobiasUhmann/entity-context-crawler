import streamlit as st

from app.pages.browse_triple_sets import render_browse_triple_sets_page
from app.pages.evaluate_model import render_evaluate_model_page
from app.pages.look_up_entities_and_relations import render_look_up_entities_and_relations_page
from app.pages.model_overview import render_model_overview_page
from app.pages.predict_entity_triples import render_predict_entity_triples_page
from app.pages.rank_triple import render_rank_triple_page
from app.pages.show_entity_contexts import render_show_entity_contexts_page
from app.pages.show_entity_triples import render_show_entity_triples_page
from app.pages.show_relation_triples import render_show_relation_triples_page


def render_index():
    """ Render the part that is common to all pages: The sidebar navigation """

    st.sidebar.header('Navigation')

    navigate_to = st.sidebar.radio('', [
        'Model Overview',
        'Look up entities and relations',
        'Browse triple sets',
        'Show entity contexts',
        'Show entity triples',
        'Show relation triples',
        'Predict entity triples',
        'Rank triple',
        'Evaluate model',
    ])

    if navigate_to == 'Model Overview':
        render_model_overview_page()
    elif navigate_to == 'Look up entities and relations':
        render_look_up_entities_and_relations_page()
    elif navigate_to == 'Browse triple sets':
        render_browse_triple_sets_page()
    elif navigate_to == 'Show entity contexts':
        render_show_entity_contexts_page()
    elif navigate_to == 'Show entity triples':
        render_show_entity_triples_page()
    elif navigate_to == 'Show relation triples':
        render_show_relation_triples_page()
    elif navigate_to == 'Predict entity triples':
        render_predict_entity_triples_page()
    elif navigate_to == 'Rank triple':
        render_rank_triple_page()
    elif navigate_to == 'Evaluate model':
        render_evaluate_model_page()
