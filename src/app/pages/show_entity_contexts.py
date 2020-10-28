import os
import pandas as pd
import random
import re
import sqlite3
import streamlit as st

from typing import Set

from app.util import load_dataset
from dao.contexts_db import select_contexts
from dao.matches_db import select_distinct_mentions
from dao.mid2rid_txt import load_mid2rid
from util.mask_contexts import mask_contexts


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

    prefix = st.text_input('Filter entities by prefix', value='Ab')

    options = ['%s (%d)' % (id2ent[ent], ent) for ent in ow_entities]
    prefixed_options = [opt for opt in options if opt.startswith(prefix)]
    prefixed_options.sort()

    selected_option = st.selectbox('Entity (ID)', prefixed_options)
    regex = r'^.+ \((\d+)\)$'  # any string followed by space and number in parentheses, e.g. "Foo bar (123)"
    entity = int(re.match(regex, selected_option).group(1))  # get number, e.g. 123

    #
    # Show contexts
    #

    st.markdown('---')

    mid2rid_txt = 'data/entity2id.txt'
    matches_db = 'data/enwiki-latest-matches.db'
    contexts_db = 'data/enwiki-latest-ow-contexts-100-500.db'

    with sqlite3.connect(matches_db) as matches_conn, \
            sqlite3.connect(contexts_db) as contexts_conn:

        entity_name = id2ent[entity]
        entity_contexts = select_contexts(contexts_conn, entity)

        mid2rid = load_mid2rid(mid2rid_txt)
        rid2mid = {rid: mid for mid, rid in mid2rid.items()}

        mentions = select_distinct_mentions(matches_conn, rid2mid[entity])
        masked_contexts = mask_contexts(entity_contexts, mentions)

    st.write('Database contains **%d contexts** for "%s"' % (len(entity_contexts), entity_name))

    data = zip(entity_contexts, masked_contexts)
    df = pd.DataFrame(data, columns=['Context', 'Masked Context'])

    truncate_contexts = st.checkbox('Truncate contexts')

    if truncate_contexts:
        st.dataframe(df)
    else:
        st.table(df)
