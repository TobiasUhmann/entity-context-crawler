import streamlit as st

from ryn.graphs.split import Dataset


@st.cache(allow_output_mutation=True)
def load_dataset() -> Dataset:
    return Dataset.load('data/oke.fb15k237_30061990_50')
