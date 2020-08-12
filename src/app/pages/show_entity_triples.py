import pandas as pd
import streamlit as st

from typing import Set

from app.util import load_dataset


def render_show_entity_triples_page():
    #
    # Sidebar
    #

    st.title('Entity triples')

    #
    # Load data
    #

    with st.spinner('Loading dataset...'):
        dataset = load_dataset()

    id2ent = dataset.id2ent
    id2rel = dataset.id2rel

    cw_triples = {(id2ent[head], id2ent[tail], id2rel[rel])
                  for head, tail, rel in dataset.cw_train.triples | dataset.cw_valid.triples}

    ow_entities: Set[str] = {id2ent[ent] for ent in dataset.ow_valid.owe}
    ow_triples = {(id2ent[head], id2ent[tail], id2rel[rel])
                  for head, tail, rel in dataset.ow_valid.triples}

    all_triples = list(cw_triples | ow_triples)

    #
    #
    #

    st.sidebar.markdown('---')

    prefix = st.sidebar.text_input('Entity prefix', value='Ab')

    filtered_entities = [entity for entity in ow_entities if entity.startswith(prefix)]
    filtered_entities.sort()

    selected_entity = st.sidebar.selectbox('Entity', filtered_entities)

    selected_entity_triples = [triple for triple in ow_triples if triple[0] == selected_entity]

    dataFrame = pd.DataFrame(selected_entity_triples, columns=['From', 'To', 'Rel'])
    st.dataframe(dataFrame)