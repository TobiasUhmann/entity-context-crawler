#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import matplotlib.pyplot as plt
import sqlite3

from collections import defaultdict
from datetime import datetime
from deepca.dumpr import dumpr
from matplotlib.widgets import Slider
from spacy.lang.en import English
from spacy.language import Language
from spacy.matcher import PhraseMatcher

FREENODE_TO_WIKIDATA_JSON = 'entity2wikidata.json'
WIKIPEDIA_XML = 'enwiki-2018-09.full.xml'
LINKS_DB = 'links.db'
MATCHES_DB = 'matches.db'


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
        INSERT INTO docs(title, content)
        VALUES(?, ?)
    '''

    cursor = matches_conn.cursor()
    cursor.execute(sql, (title, content))
    cursor.close()


def insert_match(matches_conn, mid, entity, doc_title, start_char, end_char, context):
    sql = '''
        INSERT INTO matches(mid, entity, doc, start_char, end_char, context)
        VALUES(?, ?, ?, ?, ?, ?)
    '''

    cursor = matches_conn.cursor()
    cursor.execute(sql, (mid, entity, doc_title, start_char, end_char, context))
    cursor.close()


class EntityMatcher:
    freenode_to_wikidata_json: str  # path/to/freenode_to_wikidata.json
    wikipedia_xml: str  # path/to/wikipedia.xml
    links_db: str  # path/to/links.db
    matches_db: str  # path/to/matches.db

    nlp: Language
    matcher: PhraseMatcher

    entities = defaultdict(set)  # TODO example
    statistics: dict  # {entity: absolute_frequency}, e.g. {'anarchism': 1234, 'foo': 0, ...}

    def __init__(self, freenode_labels_json, wikipedia_docs_xml, links_db, matches_db):
        self.freenode_to_wikidata_json = freenode_labels_json
        self.wikipedia_xml = wikipedia_docs_xml
        self.links_db = links_db
        self.matches_db = matches_db

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

        with sqlite3.connect(self.matches_db) as matches_conn, \
                sqlite3.connect(self.links_db) as links_conn, \
                dumpr.BatchReader(self.wikipedia_xml) as reader:

            create_docs_table(matches_conn)
            create_matches_table(matches_conn)

            for doc_count, dumpr_doc in enumerate(reader.docs):
                if dumpr_doc.content is None:
                    continue

                self.process_doc(dumpr_doc, matches_conn, links_conn, doc_count)

                #
                # Persist database rarely (takes much time) and plot statistics
                #

                if doc_count % 1000 == 0:
                    matches_conn.commit()
                    # TODO command line param
                    # self.plot_statistics()

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


def main():
    # TODO Pass file names on command line
    entity_matcher = EntityMatcher(FREENODE_TO_WIKIDATA_JSON, WIKIPEDIA_XML, LINKS_DB, MATCHES_DB)

    entity_matcher.init()
    entity_matcher.run()


if __name__ == '__main__':
    main()
