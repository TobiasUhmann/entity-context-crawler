#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import matplotlib.pyplot as plt
import sqlite3
import time

from deepca.dumpr import dumpr
from matplotlib.widgets import Slider
from spacy.lang.en import English
from spacy.language import Language
from spacy.matcher import PhraseMatcher

FREENODE_LABELS_JSON = 'entity2wikidata.json'
WIKIPEDIA_DOCS_XML = 'enwiki-2018-09.full.xml'
MATCHES_DB = 'matches.db'


class SentenceSampler:
    nlp: Language
    matcher: PhraseMatcher
    entities: dict
    statistics: dict

    def main(self):
        #
        # Init spaCy
        #

        print('Init spaCy...', end='')
        start = time.process_time()

        self.nlp = English()
        self.nlp.vocab.lex_attr_getters = {}
        self.matcher = PhraseMatcher(self.nlp.vocab)

        with open(FREENODE_LABELS_JSON, 'r') as file:
            wikidata = json.load(file)

        self.entities = {wikidata[mid]['label']: mid for mid in wikidata}
        self.statistics = {entity: 0 for entity in self.entities}

        patterns = list(self.nlp.pipe(self.entities.keys()))
        self.matcher.add('Entities', None, *patterns)

        stop = time.process_time()
        print(' Done. Took %.2fs' % (stop - start))

        #
        # For each Wikipedia document: Search for all entities and save matches to database
        #

        with sqlite3.connect(MATCHES_DB) as conn:
            self.create_db(conn)

            with dumpr.BatchReader(WIKIPEDIA_DOCS_XML) as reader:
                for counter, dumprDoc in enumerate(reader.docs):

                    if dumprDoc.content is None:
                        continue

                    doc_title = dumprDoc.meta['title']
                    print('%d: %s' % (counter, doc_title), end='')

                    self.process_doc(dumprDoc, conn)

                    #
                    # Persist database at end of doc (takes much time) and draw statistics
                    #

                    if counter % 1000 == 0:
                        conn.commit()
                        self.plot_statistics(self.statistics)

                    start_time = time.process_time()
                    stop_time = time.process_time()
                    print(' (%dms)' % ((stop_time - start_time) * 1000))


    def create_db(self, conn):
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


    def process_doc(self, dumprDoc, conn):
        doc_title = dumprDoc.meta['title']

        doc = self.nlp.make_doc(dumprDoc.content)
        matches = self.matcher(doc)

        for match_id, start, end in matches:
            span = doc[start:end]

            sql = '''
                INSERT INTO matches(mid, entity, doc, start_char, end_char, context)
                VALUES(?, ?, ?, ?, ?, ?)
            '''

            context_start = max(span.start_char - 20, 0)
            context_end = min(span.end_char + 20, len(dumprDoc.content))
            context = dumprDoc.content[context_start:context_end]

            match = (self.entities[span.text], span.text, doc_title, span.start_char, span.end_char, context)
            conn.cursor().execute(sql, match)

            self.statistics[span.text] += 1


    def plot_statistics(self, statistics):
        """
        Plot bar chart showing the absolute frequency of the entities (in descending order). Limited to
        the 100 most frequent entities. Interrupts the program.

        :param statistics: Dict containing (entity -> absolute frequency) entries.
                           Example: {'Spanish': 25, 'anarchism': 85, 'philosophy': 15', ...}
        """

        top_statistics = sorted(list(statistics.items()), key=lambda item: item[1], reverse=True)[:100]
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


if __name__ == '__main__':
    sentence_sampler = SentenceSampler()
    sentence_sampler.main()
