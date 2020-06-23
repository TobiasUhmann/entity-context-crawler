#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import json
import matplotlib.pyplot as plt
import sqlite3

from collections import defaultdict
from datetime import datetime
from matplotlib.widgets import Slider
from os import remove
from os.path import isfile
from spacy.lang.en import English
from spacy.language import Language
from spacy.matcher import PhraseMatcher

from deepca.dumpr import dumpr

#
# DEFAULT CONFIG
#

COMMIT_FREQUENCY = 1000
LIMIT_DOCS = None


#
# MAIN
#

def main():
    #
    # Parse args
    #

    parser = argparse.ArgumentParser(
        description='Match the Freenode entities (considering the link graph)',
        formatter_class=lambda prog: argparse.MetavarTypeHelpFormatter(prog, max_help_position=50, width=120))

    parser.add_argument('freenode_json', metavar='freenode-json', type=str,
                        help='path to Freenode JSON')

    parser.add_argument('wikipedia_xml', metavar='wikipedia-xml', type=str,
                        help='path to pre-processed Wikipedia XML')

    parser.add_argument('links_db', metavar='links-db', type=str,
                        help='path to links DB')

    parser.add_argument('matches_db', metavar='matches-db', type=str,
                        help='path to matches DB')

    parser.add_argument('--commit-frequency', dest='commit_frequency', default=COMMIT_FREQUENCY,
                        help='commit to database every ... docs (default: {})'.format(COMMIT_FREQUENCY))

    parser.add_argument('--in-memory', dest='in_memory', action='store_true',
                        help='build complete matches DB in memory before persisting it')

    parser.add_argument('--limit-docs', dest='limit_docs', default=LIMIT_DOCS, type=int,
                        help='terminate after ... docs (default: {})'.format(LIMIT_DOCS))

    parser.add_argument('--overwrite', dest='overwrite', action='store_true',
                        help='overwrite matches DB if it already exists')

    args = parser.parse_args()

    #
    # Print applied config
    #

    print('Applied config:')
    print('    {:20} {}'.format('Freenode JSON', args.freenode_json))
    print('    {:20} {}'.format('Wikipedia XML', args.wikipedia_xml))
    print('    {:20} {}'.format('Links DB', args.links_db))
    print('    {:20} {}'.format('Matches DB', args.matches_db))
    print()
    print('    {:20} {}'.format('Commit frequency', args.commit_frequency))
    print('    {:20} {}'.format('In memory', args.in_memory))
    print('    {:20} {}'.format('Limit docs', args.limit_docs))
    print('    {:20} {}'.format('Overwrite', args.overwrite))
    print()

    #
    # Check for input/output files
    #

    if not isfile(args.freenode_json):
        print('Freenode JSON not found')
        exit()

    if not isfile(args.wikipedia_xml):
        print('Wikipedia XML not found')
        exit()

    if not isfile(args.links_db):
        print('Links DB not found')
        exit()

    if isfile(args.matches_db):
        if args.overwrite:
            remove(args.matches_db)
        else:
            print('Matches DB already exists. Use --overwrite to overwrite it')
            exit()

    #
    # Run entity matcher
    #

    entity_matcher = EntityMatcher(args.freenode_json, args.wikipedia_xml, args.links_db, args.matches_db,
                                   args.commit_frequency, args.in_memory, args.limit_docs)

    entity_matcher.init()
    entity_matcher.run()


#
# ENTITY MATCHER
#

class EntityMatcher:
    freenode_to_wikidata_json: str
    wikipedia_xml: str
    links_db: str
    matches_db: str

    in_memory: bool
    commit_frequency: int
    limit: int

    nlp: Language
    matcher: PhraseMatcher

    entities = defaultdict(set)  # TODO example
    statistics: dict  # {entity: absolute_frequency}, e.g. {'anarchism': 1234, 'foo': 0, ...}

    def __init__(self, freenode_json, wikipedia_xml, links_db, matches_db, commit_frequency, in_memory, limit_docs):
        self.freenode_to_wikidata_json = freenode_json
        self.wikipedia_xml = wikipedia_xml
        self.links_db = links_db
        self.matches_db = matches_db

        self.commit_frequency = commit_frequency
        self.in_memory = in_memory
        self.limit = limit_docs

    def init(self):
        """
        Create English spaCy object and matcher. Furthermore, load entity labels to create entities dict and
        initialize statistics.
        """

        self.nlp = English()
        self.nlp.vocab.lex_attr_getters = {}
        self.matcher = PhraseMatcher(self.nlp.vocab)

        with open(self.freenode_to_wikidata_json, 'r') as file:
            wikidata = json.load(file)

        languages = {
            'Arabic', 'Chinese', 'Japanese', 'Dutch', 'English', 'French', 'German', 'Greek', 'Italian',
            'Latin', 'Persian', 'Spanish', 'Russian',
        }

        months = {
            'January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September',
            'October', 'November', 'December',
        }

        blacklist = languages | months

        #
        # self.entities: entity -> {(MID, Wikipedia doc title)...}
        #
        # {
        #     ...
        #     'Spider-Man': {('/m/06ys2', 'Spider-Man'), ('/m/012s1d', 'Spider-Man (2002 film)')}
        #     'Spidey': {('/m/06ys2', 'Spider-Man')}
        #     ...
        # }
        #
        # Homonyms map to multiple Freenode nodes.
        # Includes alternative names.
        #

        missing_urls = 0
        for mid in wikidata:
            labels = {wikidata[mid]['label']}
            # labels.update(wikidata[mid]['alternatives'])

            wikipedia_url = wikidata[mid]['wikipedia']
            if wikipedia_url:
                doc_title = wikipedia_url.rsplit('/', 1)[-1].replace('_', ' ').lower()

                for label in labels:
                    self.entities[label].add((mid, doc_title))
            else:
                missing_urls += 1

        print('Missing URLs: %d' % missing_urls)

        #
        #
        #

        self.statistics = {entity: 0 for entity in self.entities}

        patterns = list(self.nlp.pipe(self.entities.keys()))
        self.matcher.add('Entities', None, *patterns)

    def run(self):
        """
        Find and persist entity matches in Wikipedia documents.
        """

        if self.in_memory:
            self.__run_in_memory()
        else:
            self.__run_on_disk()

    def __run_on_disk(self):
        with sqlite3.connect(self.matches_db) as matches_conn:
            create_docs_table(matches_conn)
            create_matches_table(matches_conn)
            self.__process_wikipedia(matches_conn)
            print('{} | DONE'.format(datetime.now().strftime('%H:%M:%S')))

    def __run_in_memory(self):
        with sqlite3.connect(':memory:') as memory_conn:
            create_docs_table(memory_conn)
            create_matches_table(memory_conn)
            self.__process_wikipedia(memory_conn)

            print('{} | PERSIST'.format(datetime.now().strftime('%H:%M:%S')))
            with sqlite3.connect(self.matches_db) as matches_conn:
                for line in memory_conn.iterdump():
                    if line not in ('BEGIN;', 'COMMIT;'):  # let python handle the transactions
                        matches_conn.execute(line)

            print('{} | DONE'.format(datetime.now().strftime('%H:%M:%S')))

    def __process_wikipedia(self, matches_conn):
        with sqlite3.connect(self.links_db) as links_conn, \
                dumpr.BatchReader(self.wikipedia_xml) as reader:

            for doc_count, dumpr_doc in enumerate(reader.docs):
                if self.limit and doc_count > self.limit:
                    break

                if doc_count % self.commit_frequency == 0:
                    print('{} | COMMIT'.format(datetime.now().strftime('%H:%M:%S')))
                    matches_conn.commit()
                    # self.plot_statistics()

                if dumpr_doc.content is None:
                    continue

                self.process_doc(dumpr_doc, matches_conn, links_conn, doc_count)

    def process_doc(self, dumpr_doc, matches_conn, links_conn, doc_count):
        current_doc_title = dumpr_doc.meta['title']
        current_doc_hash = hash(current_doc_title.lower())

        #
        # Store doc in docs table
        #

        insert_doc(matches_conn, dumpr_doc.meta['title'], dumpr_doc.content)

        #
        # spaCy
        #

        doc = self.nlp.make_doc(dumpr_doc.content)
        matches = self.matcher(doc)

        #
        # Query neighbor docs
        #

        cursor = links_conn.cursor()
        cursor.execute('SELECT to_doc FROM links WHERE from_doc = ?', (current_doc_hash,))
        links_to_hashes = {row[0] for row in cursor.fetchall()}
        cursor.close()

        cursor = links_conn.cursor()
        cursor.execute('SELECT from_doc FROM links WHERE to_doc = ?', (current_doc_hash,))
        linked_from_hashes = {row[0] for row in cursor.fetchall()}
        cursor.close()

        neighbor_docs = {current_doc_hash} | links_to_hashes | linked_from_hashes

        #
        # Process all Freenode entities & save if in neighbor docs
        #

        match_count = 0
        for match_id, start, end in matches:
            entity_span = doc[start:end]
            entity = entity_span.text

            if not self.entities[entity]:
                continue

            entity_doc_title = list(self.entities[entity])[0][1]
            entity_doc = hash(entity_doc_title)
            if entity_doc not in neighbor_docs:
                continue

            mid = list(self.entities[entity])[0][0]

            context_start = max(entity_span.start_char - 20, 0)
            context_end = min(entity_span.end_char + 20, len(dumpr_doc.content))
            context = dumpr_doc.content[context_start:context_end]

            insert_match(matches_conn, mid, entity, current_doc_title,
                         entity_span.start_char, entity_span.end_char, context)

            match_count += 1
            self.statistics[entity] += 1

        print('{} | {:,} Docs | {} | {:,} neighbors | {:,} matches'.format(
            datetime.now().strftime("%H:%M:%S"), doc_count, current_doc_title, len(neighbor_docs), match_count))

    def plot_statistics(self):
        """
        Plot bar chart showing the absolute frequency of the entities (in descending order). Limited to
        the 100 most frequent entities. Interrupts the program.
        """

        top_statistics = sorted(list(self.statistics.items()), key=lambda item: item[1], reverse=True)[:200]
        entities = [item[0] for item in top_statistics]
        frequencies = [item[1] for item in top_statistics]

        visible_bars = 10

        ax_bar_chart = plt.axes([0.1, 0.2, 0.8, 0.6])
        plt.bar(entities[:visible_bars], frequencies[:visible_bars])

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
# DATABASE FUNCTIONS
#

def create_docs_table(matches_conn):
    sql = '''
        CREATE TABLE docs (
            title text,         -- Lowercase Wikipedia title
            content text,       -- Truecase article content

            PRIMARY KEY (title)
        )
    '''

    cursor = matches_conn.cursor()
    cursor.execute(sql)
    cursor.close()


def create_matches_table(matches_conn):
    sql = '''
        CREATE TABLE matches (
            mid text,           -- MID = Freebase ID, e.g. '/m/012s1d'
            entity text,        -- Wikipedia label for MID, not unique, e.g. 'Spider-Man', for debugging
            doc text,           -- Wikipedia page title, unique, e.g. 'Spider-Man (2002 film)'
            start_char integer, -- Start char position of entity match within document
            end_char integer,   -- End char position (exclusive) of entity match within document
            context text,       -- Text around match, e.g. 'Spider-Man is a 2002 American...', for debugging

            FOREIGN KEY (doc) REFERENCES docs (title),
            PRIMARY KEY (mid, doc, start_char)
        )
    '''

    cursor = matches_conn.cursor()
    cursor.execute(sql)
    cursor.close()


def insert_doc(matches_conn, title, content):
    sql = '''
        INSERT INTO docs (title, content)
        VALUES (?, ?)
    '''

    cursor = matches_conn.cursor()
    cursor.execute(sql, (title, content))
    cursor.close()


def insert_match(matches_conn, mid, entity, doc_title, start_char, end_char, context):
    sql = '''
        INSERT INTO matches (mid, entity, doc, start_char, end_char, context)
        VALUES (?, ?, ?, ?, ?, ?)
    '''

    cursor = matches_conn.cursor()
    cursor.execute(sql, (mid, entity, doc_title, start_char, end_char, context))
    cursor.close()


#
#
#

if __name__ == '__main__':
    main()
