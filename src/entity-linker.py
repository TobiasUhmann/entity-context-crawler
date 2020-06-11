#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import matplotlib.pyplot as plt
import random
import sqlite3
import re

from collections import Counter, defaultdict
from elasticsearch import Elasticsearch
from matplotlib.widgets import Slider
from os import remove
from os.path import isfile


#
# DEFAULT CONFIG
#

CONTEXT_SIZE = 1000
LIMIT_CONTEXTS = None
LIMIT_ENTITIES = None


#
# MAIN
#

def main():
    #
    # Parse args
    #

    parser = argparse.ArgumentParser(
        description='Determine how closely linked contexts of different entities are',
        formatter_class=lambda prog: argparse.MetavarTypeHelpFormatter(prog, max_help_position=50, width=120))

    parser.add_argument('matches_db', metavar='matches-db', type=str,
                        help='path to matches DB')

    parser.add_argument('contexts_db', metavar='contexts-db', type=str,
                        help='path to contexts DB')

    parser.add_argument('--context-size', dest='context_size', default=CONTEXT_SIZE, type=int,
                        help='consider ... chars on each side of the entity mention (default: {})'.format(CONTEXT_SIZE))

    parser.add_argument('--crop-sentences', dest='crop_sentences', action='store_true',
                        help='crop contexts at their sentence boundaries (instead of token boundaries)')

    parser.add_argument('--limit-contexts', dest='limit_contexts', default=LIMIT_CONTEXTS, type=int,
                        help='only process the first ... contexts for each entity (default: {})'.format(LIMIT_CONTEXTS))

    parser.add_argument('--limit-entities', dest='limit_entities', default=LIMIT_ENTITIES, type=int,
                        help='only process the first ... entities (default: {})'.format(LIMIT_ENTITIES))

    parser.add_argument('--overwrite', dest='overwrite', action='store_true',
                        help='overwrite contexts DB if it already exists')

    args = parser.parse_args()

    #
    # Print applied config
    #

    print('Applied config:')
    print('    {:20} {}'.format('Matches DB', args.matches_db))
    print('    {:20} {}'.format('Contexts DB', args.contexts_db))
    print()
    print('    {:20} {}'.format('Context size', args.context_size))
    print('    {:20} {}'.format('Crop sentences', args.crop_sentences))
    print('    {:20} {}'.format('Limit contexts', args.limit_contexts))
    print('    {:20} {}'.format('Limit entities', args.limit_entities))
    print('    {:20} {}'.format('Overwrite', args.overwrite))
    print()

    #
    # Check for input/output files
    #

    if not isfile(args.matches_db):
        print('Matches DB not found')
        exit()

    if isfile(args.contexts_db):
        if args.overwrite:
            remove(args.contexts_db)
        else:
            print('Contexts DB already exists. Use --overwrite to overwrite it')
            exit()

    #
    # Run entity linker
    #

    entity_linker = EntityLinker(args.matches_db, args.contexts_db, args.context_size, args.crop_sentences,
                                 args.limit_contexts, args.limit_entities)
    entity_linker.run()


#
# ENTITY LINKER
#

class EntityLinker:
    matches_db: str
    contexts_db: str

    context_size: int
    crop_sentences: bool
    limit_contexts: int
    limit_entities: int

    def __init__(self, matches_db, contexts_db, context_size, crop_sentences, limit_contexts, limit_entities):
        self.matches_db = matches_db
        self.contexts_db = contexts_db

        self.context_size = context_size
        self.crop_sentences = crop_sentences
        self.limit_contexts = limit_contexts
        self.limit_entities = limit_entities

    def run(self):
        es = Elasticsearch()
        es.indices.delete(index='sentence-sampler-index', ignore=[400, 404])
        with sqlite3.connect(self.matches_db) as matches_conn, \
                sqlite3.connect(self.contexts_db) as contexts_conn:

            create_contexts_table(contexts_conn)

            #
            # TRAINING
            #

            entities = select_entities(matches_conn, limit=self.limit_entities)
            for id, entity in enumerate(entities):
                print(' {:5}  {:20}'.format('TRAIN', entity))
                print('-------------------------------------------------------------------')

                contexts = select_contexts(matches_conn, entity, size=self.context_size, limit=self.limit_contexts)

                cropped_contexts = []
                for context in contexts:
                    regex = r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s' if self.crop_sentences else r'\s'
                    match = re.search(regex, context)
                    if match:
                        start = match.end()
                        end = context.rfind(re.findall(regex, context)[-1])
                        if start < end:
                            cropped_contexts.append(context[start:end])

                # cropped_contexts = [context[context.find(' ') + 1: context.rfind(' ')] for context in contexts]
                masked_contexts = [context.replace(entity, '') for context in cropped_contexts]

                train_contexts = masked_contexts[:int(0.7 * len(masked_contexts))]
                for train_context in train_contexts:
                    print(repr(train_context[:100]))
                print()

                test_contexts = masked_contexts[int(0.7 * len(masked_contexts)):]

                for i, test_context in enumerate(test_contexts):
                    insert_context(contexts_conn, entity, test_context)

                es_doc = {'entity': entity, 'context': ' '.join(train_contexts)}
                es.index(index="sentence-sampler-index", id=id, body=es_doc)
                es.indices.refresh(index="sentence-sampler-index")

            #
            # TESTING
            #

            stats = defaultdict(Counter)

            all_test_contexts = select_test_contexts(contexts_conn)
            for entity, test_context in all_test_contexts:
                print(' {:5}  {:24}  {}'.format('QUERY', entity, repr(test_context[:100])))
                print('-------------------------------------------------------------------')

                res = es.search(index="sentence-sampler-index",
                                body={"query": {"match": {'context': test_context}}})

                hits = res['hits']['hits']
                for hit in hits:
                    score = hit['_score']
                    hit_entity = hit['_source']['entity']
                    concat = repr(hit['_source']['context'][:100])
                    print(' {:5.1f}  {:24}  {}'.format(score, hit_entity, concat))
                    stats[entity][hit_entity] += 1

                print()

            #
            # STATS
            #

            for entity, stat in stats.items():
                top_stat = stat.most_common(4)
                top_stat_count = sum(stat.values())

                print('{:3} / {:3} {:30} #   '.format(stat[entity], top_stat_count, entity), end='')
                for t in top_stat:
                    print('{:3} {:30}'.format(t[1], t[0]), end='')
                print()

            statistics = {'{0} ({1})'.format(entity, sum(stats[entity].values())): stats[entity][entity] / sum(stats[entity].values())
                          for entity in entities if sum(stats[entity].values()) > 0}

            # plot_statistics(statistics)
            # plot_statistics(statistics, sort=True)


#
# DATABASE FUNCTIONS
#

def select_entities(conn, limit):
    sql = '''
        SELECT DISTINCT entity
        FROM matches
        ORDER BY RANDOM()
    '''

    cursor = conn.cursor()

    if limit:
        sql += 'LIMIT ?'
        cursor.execute(sql, (limit,))
    else:
        cursor.execute(sql)

    rows = cursor.fetchall()
    cursor.close()

    return [row[0] for row in rows]


def select_contexts(conn, entity, size, limit):
    sql = '''
        -- SELECT context = [max <size> chars] + [entity] + [max <size> chars]

        SELECT SUBSTR(content,
                      MAX(start_char + 1 - ?, 1), 
                      MIN((start_char + 1 - MAX(start_char + 1 - ?, 1)) + (end_char - start_char) + ?, length(content)))
        FROM docs INNER JOIN matches ON docs.title = matches.doc
        WHERE entity = ?
        ORDER BY RANDOM()
    '''

    cursor = conn.cursor()

    if limit:
        sql += 'LIMIT ?'
        cursor.execute(sql, (size, size, size, entity, limit))
    else:
        cursor.execute(sql, (size, size, size, entity))

    rows = cursor.fetchall()
    cursor.close()

    return [row[0] for row in rows]


def create_contexts_table(contexts_conn):
    sql = '''
        CREATE TABLE contexts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entity TEXT,
            context TEXT
        )
    '''

    cursor = contexts_conn.cursor()
    cursor.execute(sql)
    cursor.close()


def insert_context(contexts_conn, entity, context):
    sql = '''
        INSERT INTO contexts (entity, context)
        VALUES (?, ?)
    '''

    cursor = contexts_conn.cursor()
    cursor.execute(sql, (entity, context))
    cursor.close()


def select_test_contexts(contexts_conn):
    sql = '''
        SELECT entity, context
        FROM contexts
    '''

    cursor = contexts_conn.cursor()
    cursor.execute(sql)
    rows = cursor.fetchall()
    cursor.close()

    return [(row[0], row[1]) for row in rows]


#
# HELPER
#

def plot_statistics(statistics, sort=False):
    """
    Plot bar chart showing the absolute frequency of the entities (in descending order). Limited to
    the 100 most frequent entities. Interrupts the program.
    """

    statistics_list = list(statistics.items())
    top_statistics = sorted(statistics_list, key=lambda item: item[1], reverse=True)[:200] if sort else statistics_list[
                                                                                                        :200]
    entities = [item[0] for item in top_statistics]
    frequencies = [item[1] for item in top_statistics]

    visible_bars = 10

    ax_bar_chart = plt.axes([0.1, 0.2, 0.8, 0.6])
    plt.bar(entities[:visible_bars], frequencies[:visible_bars])
    plt.gca().set_ylim([0, 1])

    #
    # Sliders for scrolling through entities and showing more/less entities at a time. Update
    # chart on slider change.
    #

    def update(val):
        scroll = int(scroll_slider.val)  # new scroll position
        bars = int(visible_bars_slider.val)  # new visible bars

        ax_bar_chart.clear()
        plt.sca(ax_bar_chart)
        plt.xticks(rotation=90)
        plt.gca().set_ylim([0, 1])

        ax_bar_chart.bar(entities[scroll:(scroll + bars)],
                         frequencies[scroll:(scroll + bars)])

    ax_scroll = plt.axes([0.1, 0.9, 0.8, 0.03])
    scroll_slider = Slider(ax_scroll, '', 0, len(entities), valfmt='%d')
    scroll_slider.on_changed(update)

    ax_span = plt.axes([0.1, 0.85, 0.8, 0.03])
    visible_bars_slider = Slider(ax_span, '', 10, 100, valinit=visible_bars, valfmt='%d')
    visible_bars_slider.on_changed(update)

    #
    # Initial plotting. Updated on slider change.
    #

    plt.sca(ax_bar_chart)
    plt.xticks(rotation=90)
    plt.show()


#
#
#

if __name__ == '__main__':
    main()
