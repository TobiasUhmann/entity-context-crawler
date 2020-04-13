#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import sqlite3
import time
from random import random

from deepca.dumpr import dumpr
from spacy.lang.en import English
from spacy.matcher import PhraseMatcher

if __name__ == '__main__':

    #
    # Init spaCy
    #

    print('Init spaCy...', end='')
    start = time.process_time()

    nlp = English()
    matcher = PhraseMatcher(nlp.vocab)

    with open('entity2wikidata.json', 'r') as file:
        wikidata = json.load(file)

    terms = [wikidata[mid]['label'] for mid in wikidata]

    patterns = list(nlp.pipe(terms))
    matcher.add("Entities", None, *patterns)

    stop = time.process_time()
    print(' Done. Took %.2fs' % (stop - start))

    #
    # Create/open database and create occurrences table if not existing
    #

    with sqlite3.connect('occurrences.db') as conn:

        sql_create_occurrences_table = '''
            CREATE TABLE IF NOT EXISTS occurrences (
                mid text,       -- MID = Freebase ID, e.g. '/m/012s1d'
                entity text,    -- Wikipedia label for MID, not unique, e.g. 'Spider-Man', for debugging
                doc text,       -- Wikipedia page title, unique, e.g. 'Spider-Man (2002 film)'
                pos integer,    -- Entity occurrence within document
                context text,   -- Document text around occurrence, e.g. 'Spider-Man is a 2002 Americ', for debugging
    
                PRIMARY KEY (mid, doc, pos)
            );
        '''

        cursor = conn.cursor()
        cursor.execute(sql_create_occurrences_table)
        cursor.close()

        #
        # For each doc: Search for all entities and commit occurrences to database
        #

        with dumpr.BatchReader('enwiki-2018-09.full.xml') as reader:
            for counter, dumprDoc in enumerate(reader.docs):

                if dumprDoc.content is None:
                    continue

                doc_title = dumprDoc.meta['title']

                #
                #
                #

                start_time = time.process_time()
                print('%d: %s' % (counter, doc_title), end='')

                doc = nlp.make_doc(dumprDoc.content)
                matches = matcher(doc)

                for match_id, start, end in matches:
                    span = doc[start:end]

                    sql = '''
                        INSERT INTO occurrences(mid, entity, doc, pos, context)
                        VALUES(?, ?, ?, ?, ?)
                    '''

                    context_start = max(span.start_char - 20, 0)
                    context_end = min(span.end_char + 20, len(dumprDoc.content))
                    context = dumprDoc.content[context_start:context_end]

                    occurrence = (str(random()), span.text, doc_title, span.start_char, context)
                    conn.cursor().execute(sql, occurrence)

                #
                # Persist database commits at end of doc (takes much time)
                #

                if counter % 1000 == 0:
                    conn.commit()

                stop_time = time.process_time()
                print(' (%dms)' % ((stop_time - start_time) * 1000))
