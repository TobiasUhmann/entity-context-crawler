#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import pickle
from collections import defaultdict

import matplotlib.pyplot as plt
import sqlite3

from deepca.dumpr import dumpr
from matplotlib.widgets import Slider
from spacy.lang.en import English
from spacy.language import Language
from spacy.matcher import PhraseMatcher

FREENODE_LABELS_JSON = 'entity2wikidata.json'
WIKIPEDIA_DOCS_XML = 'enwiki-2018-09.full.xml'
MATCHES_DB = 'matches.db'


def create_db(conn):
    sql_create_matches_table = '''
        CREATE TABLE matches (
            mid text,           -- MID = Freebase ID, e.g. '/m/012s1d'
            entity text,        -- Wikipedia label for MID, not unique, e.g. 'Spider-Man', for debugging
            doc text,           -- Wikipedia page title, unique, e.g. 'Spider-Man (2002 film)'
            start_char integer, -- Start char position of entity match within document
            end_char integer,   -- End char position (exclusive) of entity match within document
            context text,       -- Text around match, e.g. 'Spider-Man is a 2002 American...', for debugging
    
            PRIMARY KEY (mid, doc, start_char)
        );
    '''

    cursor = conn.cursor()
    cursor.execute(sql_create_matches_table)
    cursor.close()


class SentenceSampler:
    freenode_labels_json: str  # path/to/freenode_labels.json
    wikipedia_docs_xml: str  # path/to/wikipedia_docs.xml
    matches_db: str  # path/to/matches.db

    nlp: Language
    matcher: PhraseMatcher

    entities = defaultdict(set)  # TODO
    statistics: dict  # {entity: absolute_frequency}, e.g. {'anarchism': 1234, 'foo': 0, ...}
    todo_list = defaultdict(set)

    def __init__(self, freenode_labels_json, wikipedia_docs_xml, matches_db):
        self.freenode_labels_json = freenode_labels_json
        self.wikipedia_docs_xml = wikipedia_docs_xml
        self.matches_db = matches_db

    def init(self):
        """
        Create English spaCy object and matcher. Furthermore, load entity labels to create entities dict and
        initialize statistics.
        """

        self.nlp = English()
        self.nlp.vocab.lex_attr_getters = {}
        self.matcher = PhraseMatcher(self.nlp.vocab)

        with open(self.freenode_labels_json, 'r') as file:
            wikidata = json.load(file)

        languages = {
            'Arabic',
            'Chinese',
            'Japanese',
            'Dutch',
            'English',
            'French',
            'German',
            'Greek',
            'Italian',
            'Latin',
            'Persian',
            'Spanish',
            'Russian',
        }
        movies = {
            '2012',
            '24',
            'Alexander',
            'It',
            'North',
        }
        months = {
            'January',
            'February',
            'March',
            'April',
            'May',
            'June',
            'July',
            'August',
            'September',
            'October',
            'November',
            'December',
        }
        other = {
            'Arab',
            'Christian'
            'House',
            'Jackson',
            'Lincoln',
            'Mary',
            'Paul',
            'Union',
            'Western',
            'York',
        }

        blacklist = languages | movies | months | other
        print(blacklist)

        # Create dict mapping entity -> {(MID, Wikipedia doc title)...}
        # Homonyms map to multiple Freenode nodes.
        # Includes alternative names.
        #
        # {
        #     ...
        #     'Spider-Man': {('/m/06ys2', 'Spider-Man'), ('/m/012s1d', 'Spider-Man (2002 film)')}
        #     'Spidey': {('/m/06ys2', 'Spider-Man')}
        #     ...
        # }

        missing_urls = 0
        for mid in wikidata:
            labels = {wikidata[mid]['label']}
            # labels.update(wikidata[mid]['alternatives'])

            wikipedia_url = wikidata[mid]['wikipedia']
            if wikipedia_url:
                doc_title = wikipedia_url.rsplit('/', 1)[-1].replace('_', ' ')

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

        with sqlite3.connect(self.matches_db) as conn:
            create_db(conn)

            with dumpr.BatchReader(self.wikipedia_docs_xml) as reader:
                for counter, dumpr_doc in enumerate(reader.docs):

                    if dumpr_doc.content is None:
                        continue

                    doc_title = dumpr_doc.meta['title']
                    print('%d: %s' % (counter, doc_title))

                    self.process_doc(dumpr_doc, conn)

                    #
                    # Persist database rarely (takes much time) and plot statistics
                    #

                    if counter % 1000 == 0:
                        conn.commit()
                        # TODO command line param
                        self.plot_statistics()

    def process_doc(self, dumpr_doc, conn):
        doc_title = dumpr_doc.meta['title']

        doc = self.nlp.make_doc(dumpr_doc.content)
        # matches = self.matcher(doc)
        matcher = PhraseMatcher(self.nlp.vocab)
        patterns = list(self.nlp.pipe(list(self.todo_list[doc_title])))
        matcher.add('Entities', None, *patterns)
        matches = matcher(doc)

        for match_id, start, end in matches:
            span = doc[start:end]
            entity = span.text

            sql = '''
                INSERT INTO matches(mid, entity, doc, start_char, end_char, context)
                VALUES(?, ?, ?, ?, ?, ?)
            '''

            context_start = max(span.start_char - 20, 0)
            context_end = min(span.end_char + 20, len(dumpr_doc.content))
            context = dumpr_doc.content[context_start:context_end]

            mid = list(self.entities[entity])[0][0]
            match = (mid, entity, doc_title, span.start_char, span.end_char, context)

            cursor = conn.cursor()
            cursor.execute(sql, match)
            cursor.close()

            self.statistics[entity] += 1

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


def dd():
    return defaultdict(set)


if __name__ == '__main__':
    # TODO Pass file names on command line
    sentence_sampler = SentenceSampler(FREENODE_LABELS_JSON, WIKIPEDIA_DOCS_XML, MATCHES_DB)

    #
    #
    #

    nodes = pickle.load(open('links.p', 'rb'))

    for node in nodes:
        if nodes[node]['redirect']:
            print(node)
            print(nodes[node])

    #
    #
    #

    with open(FREENODE_LABELS_JSON, 'r') as file:
        wikidata = json.load(file)

        for mid in wikidata:
            url = wikidata[mid]['wikipedia']
            entity = wikidata[mid]['label']
            if url:
                doc_title = url.rsplit('/', 1)[-1].replace('_', ' ')
                print(doc_title)
                if doc_title in nodes:
                    sentence_sampler.todo_list[doc_title].add(entity)
                    for doc in nodes[doc_title]['linked_by']:
                        sentence_sampler.todo_list[doc].add(entity)
                    for doc in nodes[doc_title]['links_to']:
                        sentence_sampler.todo_list[doc].add(entity)

    print(sentence_sampler.todo_list)

    sentence_sampler.init()
    sentence_sampler.run()
