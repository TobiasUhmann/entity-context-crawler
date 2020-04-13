#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import re
from random import random

import spacy
import sqlite3
import time

from deepca.dumpr import dumpr
from spacy.matcher import PhraseMatcher

if __name__ == '__main__':

    #
    # Read Wikidata JSON and create entities dict
    #

    print('Read entities...', end='')
    start = time.process_time()

    with open('entity2wikidata.json', 'r') as file:
        wikidata = json.load(file)

    entities = {}
    for mid in wikidata:
        entity = wikidata[mid]['label']
        entity_tokens = tuple(re.findall(r'\w+', entity.lower()))
        entities[entity_tokens] = (mid, entity)

    stop = time.process_time()
    print(' Done. Took %.2fs' % (stop - start))

    #
    # Init spaCy
    #

    nlp = spacy.load('en_core_web_sm')
    matcher = PhraseMatcher(nlp.vocab)

    terms = []
    for mid in wikidata:
        terms.append(wikidata[mid]['label'])

    patterns = [nlp.make_doc(text) for text in terms]
    matcher.add("Entities", None, *patterns)

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
                    # print(span.text, span.start_char, span.end_char)

                    sql = '''
                        INSERT INTO occurrences(mid, entity, doc, pos, context)
                        VALUES(?, ?, ?, ?, ?)
                    '''

                    # mid = entities[n_gram][0]
                    # entity = entities[n_gram][1]

                    context_start = max(span.start_char - 20, 0)
                    context_end = min(span.end_char + 20, len(dumprDoc.content))
                    context = dumprDoc.content[context_start:context_end]

                    occurrence = (str(random()), span.text, doc_title, span.start_char, context)
                    conn.cursor().execute(sql, occurrence)

                #
                #
                #

                # doc_title = dumprDoc.meta['title']
                # content = dumprDoc.content.lower()

                #
                # For each doc: Transform doc to lowercase token sequence. Then, for each token that is a
                #               Freebase entity, add its position tuple (doc, pos) to the global index
                #

                # doc_tokens = []
                # doc_token_positions = []
                # for match in re.finditer(r'\w+', content):
                #     doc_tokens.append(match.group())
                #     doc_token_positions.append(match.start())

                # for n in range(1, 5):
                #     for i in range(len(doc_tokens) - n + 1):
                #         n_gram = tuple(doc_tokens[i:i + n])
                #         pos = doc_token_positions[i]
                #
                #         if n_gram in entities:
                #             sql = '''
                #                 INSERT INTO occurrences(mid, entity, doc, pos, context)
                #                 VALUES(?, ?, ?, ?, ?)
                #             '''
                #
                #             mid = entities[n_gram][0]
                #             entity = entities[n_gram][1]
                #
                #             context_start = max(pos - 20, 0)
                #             context_end = min(pos + 30, len(dumprDoc.content))
                #             context = dumprDoc.content[context_start:context_end]
                #
                #             occurrence = (mid, entity, doc_title, pos, context)
                #             conn.cursor().execute(sql, occurrence)

                #
                # Persist database commits at end of doc (takes much time)
                #

                if counter % 1000 == 0:
                    conn.commit()

                stop_time = time.process_time()
                print(' (%dms)' % ((stop_time - start_time) * 1000))
