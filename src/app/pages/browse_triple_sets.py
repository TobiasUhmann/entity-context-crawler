import pickle
import random
from typing import Dict, Set

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

    ents: Set[int] = set(ent_to_label.keys())
    rels: Set[int] = set(rel_to_label.keys())

    triples = []

    #
    # Select sets
    #

    st.title('Browse triple sets')

    select_sets_expander = st.beta_expander("Select sets", expanded=True)
    with select_sets_expander:

        cols = st.beta_columns([25, 25, 25, 25])

        selected_cw_train = cols[0].checkbox('CW Train', value=True, key='ss-cwtrain')
        cols[0].markdown(f'<div style="{blue_1}">&nbsp;</div>', unsafe_allow_html=True)

        if selected_cw_train:
            cw_train_triples = [('CW Train', head, rel, tail) for head, tail, rel in dataset.cw_train.triples]
        else:
            cw_train_triples = []

        selected_cw_valid = cols[1].checkbox('CW Valid', value=True, key='ss-cwvalid')
        cols[1].markdown(f'<div style="{green_1}">&nbsp;</div>', unsafe_allow_html=True)

        if selected_cw_valid:
            cw_valid_triples = [('CW Valid', head, rel, tail) for head, tail, rel in dataset.cw_valid.triples]
        else:
            cw_valid_triples = []

        selected_ow_valid = cols[2].checkbox('OW Valid', value=True, key='ss-owvalid')
        cols[2].markdown(f'<div style="{yellow_1}">&nbsp;</div>', unsafe_allow_html=True)

        if selected_ow_valid:
            ow_valid_triples = [('OW Valid', head, rel, tail) for head, tail, rel in dataset.ow_valid.triples]
        else:
            ow_valid_triples = []

        selected_ow_test = cols[3].checkbox('OW Test', key='ss-owtest')
        cols[3].markdown(f'<div style="{red_1}">&nbsp;</div>', unsafe_allow_html=True)

        if selected_ow_test:
            ow_test_triples = [('OW Test', head, rel, tail) for head, tail, rel in dataset.ow_test.triples]
        else:
            ow_test_triples = []

        st.write('')

    #
    # Limit triples
    #

    limit_triples_expander = st.beta_expander("Limit triples (per set)", expanded=False)
    with limit_triples_expander:

        cols = st.beta_columns([33, 33, 33])

        limit_from = cols[0].number_input('From', value=0)
        limit_until = cols[1].number_input('Until', value=100)
        limit_step = cols[2].number_input('Step', value=1)

        triples = cw_train_triples[limit_from:limit_until:limit_step] + \
                  cw_valid_triples[limit_from:limit_until:limit_step] + \
                  ow_valid_triples[limit_from:limit_until:limit_step] + \
                  ow_test_triples[limit_from:limit_until:limit_step]

    #
    # Filter triples
    #

    filter_triples_expander = st.beta_expander("Filter triples", expanded=False)
    with filter_triples_expander:

        cols = st.beta_columns([33, 33, 33])

        filter_head = cols[0].radio('Filter by head', options=['Any head', 'Head ID', 'Head label contains'])
        filter_head_id = cols[0].number_input('Head ID', min_value=min(ents), max_value=max(ents), value=min(ents))
        filter_head_label = cols[0].text_input('Head label contains', value='Ab')

        if filter_head == 'Head ID':
            triples = [(set_, head, rel, tail) for set_, head, rel, tail in triples
                       if head == filter_head_id]
        elif filter_head == 'Head label contains':
            triples = [(set_, head, rel, tail) for set_, head, rel, tail in triples
                       if filter_head_label in ent_to_label[head]]

        filter_rel = cols[1].radio('Filter by relation', options=['Any relation', 'Relation ID', 'Relation label contains'])
        filter_rel_id = cols[1].number_input('Relation ID', min_value=min(rels), max_value=max(rels), value=min(rels))
        filter_rel_label = cols[1].text_input('Relation label contains', value='/a')

        if filter_rel == 'Relation ID':
            triples = [(set_, head, rel, tail) for set_, head, rel, tail in triples
                       if rel == filter_rel_id]
        elif filter_rel == 'Relation label contains':
            triples = [(set_, head, rel, tail) for set_, head, rel, tail in triples
                       if filter_rel_label in rel_to_label[rel]]

        filter_tail = cols[2].radio('Filter by tail', options=['Any tail', 'Tail ID', 'Tail label contains'])
        filter_tail_id = cols[2].number_input('Tail ID', min_value=min(ents), max_value=max(ents), value=min(ents))
        filter_tail_label = cols[2].text_input('Tail label contains', value='Ab')

        if filter_tail == 'Tail ID':
            triples = [(set_, head, rel, tail) for set_, head, rel, tail in triples
                       if tail == filter_tail_id]
        elif filter_tail == 'Tail label contains':
            triples = [(set_, head, rel, tail) for set_, head, rel, tail in triples
                       if filter_tail_label in ent_to_label[tail]]

    #
    # Shuffle triples
    #

    shuffle_triples_expander = st.beta_expander("Shuffle triples", expanded=False)
    with shuffle_triples_expander:

        shuffle = st.checkbox('Shuffle')

        if shuffle:
            random.shuffle(triples)

    #
    # Print triples
    #

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

    columns = ['Set', 'Head', 'Head CW/OW', 'Head Label', 'Rel', 'Rel Label', 'Tail', 'Tail CW/OW', 'Tail Label']
    df = pd.DataFrame(data, columns=columns)
    df = df.style.apply(background_color, axis=1)
    st.dataframe(df)


def ent_type(dataset: split.Dataset, ent: int) -> str:
    if ent in dataset.ow_test.owe:
        return 'OW Test'
    elif ent in dataset.ow_valid.owe:
        return 'OW Valid'
    else:
        return 'CW'


@st.cache(allow_output_mutation=True)
def load_dataset(dataset_pickle: str) -> split.Dataset:
    with open(dataset_pickle, 'rb') as fh:
        dataset = pickle.load(fh)

    return dataset
