import os
import random
import re
from typing import Set

import pandas as pd
import streamlit as st

from app.util import load_dataset


def render_show_entity_contexts_page():

    #
    # Load open world entities
    #

    with st.spinner('Loading dataset...'):
        dataset = load_dataset()

    id2ent = dataset.id2ent

    ow_entities: Set[int] = dataset.ow_valid.owe

    #
    # Sidebar: Random seed & PYTHONHASHSEED
    #

    st.sidebar.markdown('---')

    random_seed = st.sidebar.number_input('Random seed', value=0)
    random.seed(random_seed)

    st.sidebar.markdown('PYTHONHASHSEED = %s' % os.getenv('PYTHONHASHSEED'))

    #
    # Entity prefix input & Entity name selection
    #

    st.title('Show entity contexts')

    prefix = st.text_input('Entity prefix', value='Ab')

    options = ['%s (%d)' % (id2ent[ent], ent) for ent in ow_entities]
    prefixed_options = [opt for opt in options if opt.startswith(prefix)]
    prefixed_options.sort()

    selected_option = st.selectbox('Entity', prefixed_options)
    regex = r'[\w\s]+ \((\d+)\)'  # get 42 from "John Doe (42)"
    selected_entity = int(re.match(regex, selected_option).group(1))

    #
    # Show contexts
    #

    st.markdown('---')

    
