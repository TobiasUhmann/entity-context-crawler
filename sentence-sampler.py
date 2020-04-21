#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import sqlite3
import time

import matplotlib.pyplot as plt
import numpy as np
from deepca.dumpr import dumpr
from matplotlib.widgets import Slider
from spacy.lang.en import English
from spacy.matcher import PhraseMatcher

if __name__ == '__main__':

    #
    # Init spaCy
    #

    print('Init spaCy...', end='')
    start = time.process_time()

    nlp = English()
    nlp.vocab.lex_attr_getters = {}
    matcher = PhraseMatcher(nlp.vocab)

    with open('entity2wikidata.json', 'r') as file:
        wikidata = json.load(file)

    entities = {wikidata[mid]['label']: mid for mid in wikidata}
    statistics = {entity: 0 for entity in entities}

    patterns = list(nlp.pipe(entities.keys()))
    matcher.add("Entities", None, *patterns)

    stop = time.process_time()
    print(' Done. Took %.2fs' % (stop - start))

    #
    # Create/open database and create occurrences table if not existing
    #

    with sqlite3.connect('occurrences.db') as conn:

        sql_create_occurrences_table = '''
            CREATE TABLE IF NOT EXISTS occurrences (
                mid text,           -- MID = Freebase ID, e.g. '/m/012s1d'
                entity text,        -- Wikipedia label for MID, not unique, e.g. 'Spider-Man', for debugging
                doc text,           -- Wikipedia page title, unique, e.g. 'Spider-Man (2002 film)'
                start_char integer, -- Start char position of entity occurrence within document
                end_char integer,   -- End char position (exclusive) of entity occurrence within document
                context text,       -- Text around occurrence, e.g. 'Spider-Man is a 2002 American...', for debugging
    
                PRIMARY KEY (mid, doc, start_char)
            );
        '''

        cursor = conn.cursor()
        cursor.execute(sql_create_occurrences_table)
        cursor.close()

        #
        # For each doc: Search for all entities and save occurrences to database
        #

        with dumpr.BatchReader('enwiki-2018-09.full.xml') as reader:
            for counter, dumprDoc in enumerate(reader.docs):

                if dumprDoc.content is None:
                    continue

                doc_title = dumprDoc.meta['title']

                #
                # Search for entities and save occurrences to database (in memory)
                #

                start_time = time.process_time()
                print('%d: %s' % (counter, doc_title), end='')

                doc = nlp.make_doc(dumprDoc.content)
                matches = matcher(doc)

                for match_id, start, end in matches:
                    span = doc[start:end]

                    sql = '''
                        INSERT INTO occurrences(mid, entity, doc, start_char, end_char, context)
                        VALUES(?, ?, ?, ?, ?, ?)
                    '''

                    context_start = max(span.start_char - 20, 0)
                    context_end = min(span.end_char + 20, len(dumprDoc.content))
                    context = dumprDoc.content[context_start:context_end]

                    occurrence = (entities[span.text], span.text, doc_title, span.start_char, span.end_char, context)
                    conn.cursor().execute(sql, occurrence)

                    statistics[span.text] += 1

                #
                # Persist database at end of doc (takes much time) and draw statistics
                #

                if counter % 1000 == 0:
                    conn.commit()

                    top_statistics = sorted(list(statistics.items()), key=lambda tup: tup[1], reverse=True)[:100]

                    fig, ax = plt.subplots()

                    xs = [stat[0] for stat in top_statistics]
                    ys = [stat[1] for stat in top_statistics]

                    span = 10
                    plt.bar(xs[:span], ys[:span])

                    def update(val):
                        scroll_pos = int(val)

                        ax.clear()
                        plt.sca(ax)
                        plt.xticks(rotation=45)

                        ax.bar(xs[scroll_pos: scroll_pos + span], ys[scroll_pos: scroll_pos + span])
                        fig.canvas.draw_idle()

                    ax_scroll = plt.axes([0.1, 0.9, 0.8, 0.03])
                    slider = Slider(ax_scroll, '', 0, len(xs) - span, valfmt='%d')
                    slider.on_changed(update)

                    plt.sca(ax)
                    plt.xticks(rotation=45)
                    plt.show()

                stop_time = time.process_time()
                print(' (%dms)' % ((stop_time - start_time) * 1000))
