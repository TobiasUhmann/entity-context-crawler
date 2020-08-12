import pandas as pd
import streamlit as st

from typing import Set

from app.util import load_dataset


def render_show_entity_triples_page():
    """
    Render UI specific to "Show entity triples" page
    """

    st.title('Show entity triples')

    #
    # Load data
    #

    with st.spinner('Loading dataset...'):
        dataset = load_dataset()

    id2ent = dataset.id2ent
    id2rel = dataset.id2rel

    cw_entities: Set[str] = {id2ent[ent] for ent in dataset.cw_train.owe}
    cw_triples = {(id2ent[head], id2ent[tail], id2rel[rel])
                  for head, tail, rel in dataset.cw_train.triples | dataset.cw_valid.triples}

    ow_entities: Set[str] = {id2ent[ent] for ent in dataset.ow_valid.owe}
    ow_triples = {(id2ent[head], id2ent[tail], id2rel[rel])
                  for head, tail, rel in dataset.ow_valid.triples}

    all_entities = cw_entities | ow_entities

    #
    #
    #

    st.sidebar.markdown('---')

    entity_selection = st.sidebar.selectbox('', [
        'Closed world entities',
        'Open world entities',
        'All entities'
    ])

    prefix = st.sidebar.text_input('Entity prefix', value='Abr')

    if entity_selection == 'Closed world entities':
        filtered_entities = [ent for ent in cw_entities if ent.startswith(prefix)]
    elif entity_selection == 'Open world entities':
        filtered_entities = [ent for ent in ow_entities if ent.startswith(prefix)]
    elif entity_selection == 'All entities':
        filtered_entities = [ent for ent in all_entities if ent.startswith(prefix)]
    else:
        raise

    filtered_entities.sort()

    selected_entity = st.sidebar.selectbox('Entity', filtered_entities)

    selected_entity_triples = [triple for triple in ow_triples if triple[0] == selected_entity]

    dataFrame = pd.DataFrame(selected_entity_triples, columns=['From', 'To', 'Rel'])
    st.dataframe(dataFrame)