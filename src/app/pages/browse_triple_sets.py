import pickle
from typing import Dict

import pandas as pd
import streamlit as st
from ryn.graphs import split

blue_1 = 'background-color: #7986cb'
blue_2 = 'background-color: #9fa8da'
green_1 = 'background-color: #81c784'
green_2 = 'background-color: #a5d6a7'
yellow_1 = 'background-color: #fff176'
yellow_2 = 'background-color: #fff59d'
red_1 = 'background-color: #ff8a65'
red_2 = 'background-color: #ffab91'


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

    #
    # Main
    #

    st.title('Browse triple sets')

    st.header('Select sets')

    cols = st.beta_columns([25, 25, 25, 25])

    selected_cw_train = cols[0].checkbox('CW Train', value=True, key='ss-cwtrain')
    cols[0].markdown(f'<div style="{blue_1}">&nbsp;</div>', unsafe_allow_html=True)

    selected_cw_valid = cols[1].checkbox('CW Valid', value=True, key='ss-cwvalid')
    cols[1].markdown(f'<div style="{green_1}">&nbsp;</div>', unsafe_allow_html=True)

    selected_ow_valid = cols[2].checkbox('OW Valid', value=True, key='ss-owvalid')
    cols[2].markdown(f'<div style="{yellow_1}">&nbsp;</div>', unsafe_allow_html=True)

    selected_ow_test = cols[3].checkbox('OW Test', key='ss-owtest')
    cols[3].markdown(f'<div style="{red_1}">&nbsp;</div>', unsafe_allow_html=True)

    #
    # Limit triples
    #

    st.write('')
    st.header('Limit triples')

    cols = st.beta_columns([33, 33, 33])

    limit_from = cols[0].number_input('From', value=0, key='lt-from')
    limit_until = cols[1].number_input('Until', value=1000000, key='lt-until')
    limit_step = cols[2].number_input('Step', value=100, key='lt-step')

    #
    # Show triples
    #

    triples = []

    if selected_cw_train:
        triples += [('CW Train', head, rel, tail) for head, tail, rel in dataset.cw_train.triples]

    if selected_cw_valid:
        triples += [('CW Valid', head, rel, tail) for head, tail, rel in dataset.cw_valid.triples]

    if selected_ow_valid:
        triples += [('OW Valid', head, rel, tail) for head, tail, rel in dataset.ow_valid.triples]

    if selected_ow_test:
        triples += [('OW Test', head, rel, tail) for head, tail, rel in dataset.ow_test.triples]

    triples = triples[limit_from:limit_until:limit_step]
    print(len(triples))

    data = [(set,
             head, ent_type(dataset, head), ent_to_label[head],
             rel, rel_to_label[rel],
             tail, ent_type(dataset, tail), ent_to_label[tail])
            for set, head, rel, tail in triples]

    def background_color(row):
        if row.Set == 'CW Train':
            return [blue_1] + [blue_2] * 3 + [blue_1] * 2 + [blue_2] * 3
        elif row.Set == 'CW Valid':
            return [green_1] + [green_2] * 3 + [green_1] * 2 + [green_2] * 3
        elif row.Set == 'OW Valid':
            return [yellow_1] + [yellow_2] * 3 + [yellow_1] * 2 + [yellow_2] * 3
        elif row.Set == 'OW Test':
            return [red_1] + [red_2] * 3 + [red_1] * 2 + [red_2] * 3

    columns = ['Set', 'Head', 'HW', 'Head Label', 'Rel', 'Rel Label', 'Tail', 'TW', 'Tail Label']
    df = pd.DataFrame(data, columns=columns)
    df = df.style.apply(background_color, axis=1)
    st.dataframe(df)


def ent_type(dataset, ent) -> str:
    return 'OW' if ent in dataset.ow_valid.owe else 'CW'


@st.cache(allow_output_mutation=True)
def load_dataset(dataset_pickle: str) -> split.Dataset:
    with open(dataset_pickle, 'rb') as fh:
        dataset = pickle.load(fh)

    return dataset
