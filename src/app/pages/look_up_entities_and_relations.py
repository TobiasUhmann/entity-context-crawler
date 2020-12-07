import pickle
from typing import Dict, List, Set

import streamlit as st
from ryn.graphs import split


def render_look_up_entities_and_relations_page():
    #
    # Sidebar
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

    ents = set(ent_to_label.keys())
    rels = set(rel_to_label.keys())

    #
    # Main
    #

    st.title('Look up entities and relations')

    render_ent_by_id_section(dataset, ent_to_label, ents)
    render_ent_by_label_section(dataset, ent_to_label, ents)
    render_rel_by_id_section(rel_to_label, rels)


def render_ent_by_id_section(dataset: split.Dataset, ent_to_label: Dict[int, str], ents: Set[int]) -> None:
    st.header('Entity by ID')

    cols = st.beta_columns([25, 65, 10])
    ent = cols[0].number_input('Entity ID', key='ebi-id',
                               min_value=min(ents), max_value=max(ents), value=min(ents))
    cols[1].text_input('Entity Label', key='ebi-label', value=ent_to_label[ent])
    cols[2].text_input('CW/OW', key='ebi-cwow', value=ent_type(dataset, ent))


def render_ent_by_label_section(dataset: split.Dataset, ent_to_label: Dict[int, str], ents: Set[int]) -> None:
    st.header('Entity by label')

    cols = st.beta_columns([15, 60, 15, 10])

    infix = cols[0].text_input('Label contains', key='ebl-infix', value='Ab')

    all_ents_with_labels = [(ent, ent_to_label[ent]) for ent in ents]
    filtered_ents_with_labels = [(ent, label) for ent, label in all_ents_with_labels if infix in label]
    filtered_ents_with_labels.sort(key=lambda x: x[1])

    ent = cols[1].selectbox('Entity label', key='ebl-label',
                            options=[ent for ent, label in filtered_ents_with_labels],
                            format_func=lambda option: ent_to_label[option])

    cols[2].text_input('Entity ID', key='ebl-id', value=ent)
    cols[3].text_input('CW/OW', key='ebl-cwow', value=ent_type(dataset, ent))


def render_rel_by_id_section(rel_to_label: Dict[int, str], rels: Set[int]) -> None:
    st.header('Relation by ID')

    cols = st.beta_columns([25, 75])
    rel = cols[0].number_input('Relation ID', key='rbi-id',
                               min_value=min(rels), max_value=max(rels), value=min(rels))
    cols[1].text_input('Relation Label', key='rbi-label', value=rel_to_label[rel])


def ent_type(dataset, ent) -> str:
    return 'OW' if ent in dataset.ow_valid.owe else 'CW'


@st.cache(allow_output_mutation=True)
def load_dataset(dataset_pickle: str) -> split.Dataset:
    with open(dataset_pickle, 'rb') as fh:
        dataset = pickle.load(fh)

    return dataset
