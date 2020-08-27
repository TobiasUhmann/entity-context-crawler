import pandas as pd
import streamlit as st


def render_model_overview_page():
    st.title('Model Overview')

    data = [
        ('Baseline 10', 0.0325,
         'Searches for most similar entity (in terms of TF-IDF) and assumes that the similar entity\'s triples also apply to the query entity. An entity is characterized by 10 text contexts with 500 characters each.'),
        ('Baseline 100', 0.0697,
         'Searches for most similar entity (in terms of TF-IDF) and assumes that the similar entity\'s triples also apply to the query entity. An entity is characterized by 100 text contexts with 500 characters each.')
    ]

    df = pd.DataFrame(data, columns=['Model', 'mAP', 'Info'])
    st.table(df)
