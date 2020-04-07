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
    # Read entities from JSON
    #

    print('Read entities...', end='')
    start = time.process_time()

    with open('entity2wikidata.json', 'r') as file:
        entities_dict = json.load(file)

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

                start = time.process_time()
                doc_title = doc.meta['title']
                print('%d: %s' % (counter, doc_title), end='')

                #
                # Create index that lists all occurrences for each token in the doc
                #

                index = defaultdict(list)
                for match in re.compile('\w+').finditer(doc.content):
                    index[match.group()].append(match.start())

                #
                # For each entity: Commit all occurrences (possibly none) to database
                # In case of multi-token entity: Check for occurrence of complete entity
                #

                for mid in entities_dict:
                    entity = entities_dict[mid]['label']
                    entity_tokens = re.compile('\w+').findall(entity)

                    for pos in index[entity_tokens[0]]:
                        if len(entity_tokens) > 1 and not doc.content.startswith(entity, pos):
                            continue

                        sql = '''
                            INSERT INTO occurrences(mid, entity, doc, pos, context)
                            VALUES(?, ?, ?, ?, ?)
                        '''

                        context_start = max(pos - 20, 0)
                        context_end = min(pos + 30, len(doc.content))

                        occurrence = (mid, entity, doc_title, pos, doc.content[context_start:context_end])
                        conn.cursor().execute(sql, occurrence)

                #
                # Persist database commits at end of doc (takes much time)
                #

                conn.commit()

                stop = time.process_time()
                print(' (%dms)' % ((stop - start) * 1000))
