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

    cw_ents: Set[int] = dataset.cw_train.owe
    ow_ents: Set[int] = dataset.ow_valid.owe
    all_ents = cw_ents | ow_ents

    cw_entities: Set[str] = {id2ent[ent] for ent in dataset.cw_train.owe}
    cw_triples = {(id2ent[head], id2ent[tail], id2rel[rel])
                  for head, tail, rel in dataset.cw_train.triples | dataset.cw_valid.triples}

    ow_entities: Set[str] = {id2ent[ent] for ent in dataset.ow_valid.owe}
    ow_triples = {(id2ent[head], id2ent[tail], id2rel[rel])
                  for head, tail, rel in dataset.ow_valid.triples}

    all_entities = cw_entities | ow_entities
    all_triples = cw_triples | ow_triples

    #
    #
    #

    st.sidebar.markdown('---')

    options = [
        'All entities (%d)' % len(all_ents),
        'Closed world entities (%d)' % len(cw_ents),
        'Open world entities (%d)' % len(ow_ents)
    ]

    entity_selection = st.sidebar.selectbox('Entity set', options)

    prefix = st.sidebar.text_input('Entity prefix', value='Ab')

    if entity_selection == options[0]:
        selected_ents = all_ents
    elif entity_selection == options[1]:
        selected_ents = cw_ents
    elif entity_selection == options[2]:
        selected_ents = ow_ents
    else:
        raise

    ent_names = [id2ent[ent] for ent in selected_ents]
    filtered_ent_names = [ent for ent in ent_names if ent.startswith(prefix)]
    filtered_ent_names.sort()

    selected_entity = st.sidebar.selectbox('Entity', filtered_ent_names)

    def highlight(ent_name):
        color = "blue" if ent_name in cw_entities else "green"
        return "color: white; background-color: %s" % color

    selected_entity_triples = [triple for triple in all_triples if triple[0] == selected_entity]
    dataFrame = pd.DataFrame(selected_entity_triples, columns=['From', 'To', 'Rel'])
    dataFrame = dataFrame.style.applymap(highlight)
    st.dataframe(dataFrame)

    selected_entity_triples = [triple for triple in all_triples if triple[1] == selected_entity]
    dataFrame = pd.DataFrame(selected_entity_triples, columns=['From', 'To', 'Rel'])
    dataFrame = dataFrame.style.applymap(highlight)
    st.dataframe(dataFrame)

    #
    # Misc
    #

    st.sidebar.markdown('---')
    st.sidebar.markdown('**Note:** Entity names are not unique')