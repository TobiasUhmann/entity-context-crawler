#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import re
import sqlite3
import time

from collections import defaultdict

from deepca.dumpr import dumpr

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
        entity = entity.lower()
        entity = tuple(re.findall(r'\w+', entity))
        entities[entity] = mid

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
            for counter, doc in enumerate(reader.docs):

                if doc.content is None:
                    continue

                doc_title = doc.meta['title']
                content = doc.content.lower()

                start = time.process_time()
                print('%d: %s' % (counter, doc_title), end='')

                #
                # For each doc: Transform doc to lowercase token sequence. Then, for each token that is a
                #               Freebase entity, add its position tuple (doc, pos) to the global index
                #

                doc_tokens = []
                doc_token_positions = []
                for match in re.finditer(r'\w+', content):
                    doc_tokens.append(match.group())
                    doc_token_positions.append(match.start())

                for doc_token, pos in zip(doc_tokens, doc_token_positions):
                    one_gram = (doc_token,)

                    if one_gram in entities:
                        sql = '''
                            INSERT INTO occurrences(mid, entity, doc, pos, context)
                            VALUES(?, ?, ?, ?, ?)
                        '''

                        context_start = max(pos - 20, 0)
                        context_end = min(pos + 30, len(doc.content))

                        occurrence = (entities[one_gram], doc_token, doc_title, pos, doc.content[context_start:context_end])
                        conn.cursor().execute(sql, occurrence)

                #
                # Persist database commits at end of doc (takes much time)
                #

                if counter % 1000 == 0:
                    conn.commit()

                stop = time.process_time()
                print(' (%dms)' % ((stop - start) * 1000))







    #
    # For each doc: Transform doc to lowercase token sequence. Then, for each token that is a
    #               Freebase entity, add its position tuple (doc, pos) to the global index
    #

    print('Build index...', end='')
    start = time.process_time()

    with dumpr.BatchReader('enwiki-2018-09.full.xml') as reader:
        for counter, doc in enumerate(reader.docs):
            if doc.content is None:
                continue

            doc_title = doc.meta['title']
            content = doc.content.lower()

            # start = time.process_time()
            # print('%d: %s' % (counter, doc_title), end='')

            doc_tokens = []
            doc_token_positions = []
            for match in re.finditer(r'\w+', content):
                doc_tokens.append(match.group())
                doc_token_positions.append(match.start())

            for doc_token, doc_token_position in zip(doc_tokens, doc_token_positions):
                one_gram = (doc_token,)
                if one_gram in entities:
                    entities[one_gram].add((doc_title, doc_token_position))

            # stop = time.process_time()
            # print(' (%dms)' % ((stop - start) * 1000))

    stop = time.process_time()
    print(' Done. Took %.2fs' % (stop - start))