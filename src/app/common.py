import pickle

import streamlit as st
from ryn.graphs import split


# @st.cache(allow_output_mutation=True)
def load_dataset(dataset_dir: str) -> split.Dataset:
    """
    :param dataset_dir: Path to Ryn dataset directory
    """

    return split.Dataset.load(path=dataset_dir)


@st.cache(allow_output_mutation=True)
def load_dataset_pickle(dataset_pickle: str) -> split.Dataset:
    with open(dataset_pickle, 'rb') as fh:
        dataset = pickle.load(fh)

    return dataset


def ent_type(dataset: split.Dataset, ent: int) -> str:
    if ent in dataset.ow_test.owe:
        return 'OW Test'
    elif ent in dataset.ow_valid.owe:
        return 'OW Valid'
    else:
        return 'CW'
