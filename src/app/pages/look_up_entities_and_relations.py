import pickle
from typing import Dict

import streamlit as st
from ryn.graphs import split


def render_look_up_entities_and_relations_page():

    #
    # Sidebar input
    #

    st.sidebar.header('Params')

    dataset_pickle = st.sidebar.text_input('Dataset Pickle File', 'data/oke.fb15k237_30061990_50.p')

    #
    # Load dataset
    #

    with st.spinner('Loading dataset...'):
        dataset: split.Dataset = load_dataset(dataset_pickle)

    ent_to_label: Dict[int, str] = dataset.id2ent
    rel_to_label: Dict[int, str] = dataset.id2rel

    #
    # Main input
    #

    st.title('Look up entities and relations')

    st.header('Look up entity by ID')

    cols = st.beta_columns(3)

    ents = ent_to_label.keys()
    ent = cols[0].number_input('Entity ID', min_value=min(ents), max_value=max(ents), value=min(ents))

    cols[1].text_input('Entity Label', value=ent_to_label[ent])
    cols[2].text_input('CW/OW', value='OW' if ent in dataset.ow_valid.owe else 'CW')


@st.cache(allow_output_mutation=True)
def load_dataset(dataset_pickle: str) -> split.Dataset:
    with open(dataset_pickle, 'rb') as fh:
        dataset = pickle.load(fh)

    return dataset
