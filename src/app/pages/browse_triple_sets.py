import pickle
from typing import Dict, Set

import pandas as pd
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

    st.header('Select sets')
    cols = st.beta_columns([25, 25, 25, 25])

    selected_cw_train = cols[0].checkbox('CW Train', value=True)
    cols[0].markdown('<div style="background-color: #42a5f5">&nbsp;</div>', unsafe_allow_html=True)

    selected_cw_valid = cols[1].checkbox('CW Valid', value=True)
    cols[1].markdown('<div style="background-color: #9ccc65">&nbsp;</div>', unsafe_allow_html=True)

    selected_ow_valid = cols[2].checkbox('OW Valid', value=True)
    cols[2].markdown('<div style="background-color: #ffee58">&nbsp;</div>', unsafe_allow_html=True)

    selected_ow_test = cols[3].checkbox('OW Test')
    cols[3].markdown('<div style="background-color: #ff7043">&nbsp;</div>', unsafe_allow_html=True)

    #
    # Filter
    #

    st.write('')
    st.header('Filter triples')
    st.write('test')

    #
    # Show triples
    #

    triples = [(head, rel, tail) for head, tail, rel in dataset.cw_train.triples]

    # def truth(triple: Triple):
    #     if triple in pred_triples and triple in actual_triples:
    #         return 'TP'
    #     elif triple in pred_triples and triple not in actual_triples:
    #         return 'FP'
    #     elif triple not in pred_triples and triple in actual_triples:
    #         return 'FN'
    #     elif triple not in pred_triples and triple not in actual_triples:
    #         return 'TN'
    #     else:
    #         raise AssertionError()

    data = [(head, ent_type(dataset, head), ent_to_label[head],
             rel, rel_to_label[rel],
             tail, ent_type(dataset, tail), ent_to_label[tail])
            for head, rel, tail in triples]

    df = pd.DataFrame(data, columns=['Head', '', 'Head Label', 'Rel', 'Rel Label', 'Tail', '', 'Tail Label'])
    # df = df.style.apply(background_color, axis=1)
    st.dataframe(df)


def ent_type(dataset, ent) -> str:
    return 'OW' if ent in dataset.ow_valid.owe else 'CW'


@st.cache(allow_output_mutation=True)
def load_dataset(dataset_pickle: str) -> split.Dataset:
    with open(dataset_pickle, 'rb') as fh:
        dataset = pickle.load(fh)

    return dataset
