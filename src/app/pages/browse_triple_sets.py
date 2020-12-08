import pickle
from typing import Dict, List, Set

import streamlit as st
from ryn.graphs import split


def render_browse_triple_sets_page():
    #
    # Sidebar
    #

    st.sidebar.header('Params')

    dataset_pickle = st.sidebar.text_input('Dataset Pickle File', 'data/oke.fb15k237_30061990_50.p')

    #
    # Load dataset
    #

    dataset: split.Dataset = load_dataset(dataset_pickle)

    ent_to_label: Dict[int, str] = dataset.id2ent
    rel_to_label: Dict[int, str] = dataset.id2rel

    ents: Set[int] = set(ent_to_label.keys())
    rels: Set[int] = set(rel_to_label.keys())

    #
    # Main
    #

    st.title('Browse triple sets')

    


@st.cache(allow_output_mutation=True)
def load_dataset(dataset_pickle: str) -> split.Dataset:
    with open(dataset_pickle, 'rb') as fh:
        dataset = pickle.load(fh)

    return dataset
