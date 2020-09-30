import json
import matplotlib.pyplot as plt
import os
import sqlite3

from argparse import ArgumentParser, Namespace
from collections import defaultdict
from datetime import datetime
from matplotlib.widgets import Slider
from os import remove
from os.path import isfile
from spacy.lang.en import English
from spacy.language import Language
from spacy.matcher import PhraseMatcher

from deepca.dumpr import dumpr

from dao.links_db import select_pages_linking_to, select_pages_linked_from
from dao.matches_db import insert_page, create_pages_table, create_matches_table, insert_match, Page, Match


def add_parser_args(parser: ArgumentParser):
    """
    Add arguments to arg parser:
        freenode-json
        wiki-xml
        links-db
        matches-db
        --commit-frequency
        --in-memory
        --limit-docs
        --overwrite
    """

    parser.add_argument('freenode_json', metavar='freenode-json',
                        help='Path to input Freenode JSON')

    parser.add_argument('wiki_xml', metavar='wiki-xml',
                        help='Path to input pre-processed Wikipedia XML')

    parser.add_argument('links_db', metavar='links-db',
                        help='Path to input links DB')

    parser.add_argument('matches_db', metavar='matches-db',
                        help='Path to output matches DB')

    default_commit_frequency = None
    parser.add_argument('--commit-frequency', dest='commit_frequency', type=int, metavar='INT',
                        default=default_commit_frequency,
                        help='Commit to database every ... pages instead of committing at the end only'
                             ' (default: {})'.format(default_commit_frequency))

    parser.add_argument('--in-memory', dest='in_memory', action='store_true',
                        help='Build complete matches DB in memory before persisting it')

    default_limit_docs = None
    parser.add_argument('--limit-pages', dest='limit_pages', type=int, metavar='INT', default=default_limit_docs,
                        help='Early stop after ... pages (default: {})'.format(default_limit_docs))

    parser.add_argument('--overwrite', dest='overwrite', action='store_true',
                        help='Overwrite matches DB if it already exists')


def run(args: Namespace):
    """
    - Print applied config
    - Check if files already exist
    - Run actual program
    """

    freenode_json = args.freenode_json
    wiki_xml = args.wiki_xml
    links_db = args.links_db
    matches_db = args.matches_db

    commit_frequency = args.commit_frequency
    in_memory = args.in_memory
    limit_pages = args.limit_pages
    overwrite = args.overwrite

    python_hash_seed = os.getenv('PYTHONHASHSEED')

    #
    # Print applied config
    #

    print('Applied config:')
    print('    {:20} {}'.format('freenode-json', freenode_json))
    print('    {:20} {}'.format('wiki-xml', wiki_xml))
    print('    {:20} {}'.format('links-db', links_db))
    print('    {:20} {}'.format('matches-db', matches_db))
    print()
    print('    {:20} {}'.format('--commit-frequency', commit_frequency))
    print('    {:20} {}'.format('--in-memory', in_memory))
    print('    {:20} {}'.format('--limit-pages', limit_pages))
    print('    {:20} {}'.format('--overwrite', overwrite))
    print()
    print('    {:20} {}'.format('PYTHONHASHSEED', python_hash_seed))
    print()

    #
    # Check if files already exist
    #

    if not isfile(freenode_json):
        print('Freenode JSON not found')
        exit()

    if not isfile(wiki_xml):
        print('Wikipedia XML not found')
        exit()

    if not isfile(links_db):
        print('Links DB not found')
        exit()

    if isfile(matches_db):
        if overwrite:
            remove(matches_db)
        else:
            print('Matches DB already exists, use --overwrite to overwrite it')
            exit()

    #
    # Run actual program
    #

    entity_matcher = EntityMatcher(freenode_json, wiki_xml, links_db, matches_db, commit_frequency, in_memory,
                                   limit_pages)

    entity_matcher.init()
    entity_matcher.run()


#
# ENTITY MATCHER
#

class EntityMatcher:
    freenode_to_wikidata_json: str
    wiki_xml: str
    links_db: str
    matches_db: str

    in_memory: bool
    commit_frequency: int
    limit: int

    nlp: Language
    matcher: PhraseMatcher

    entities = defaultdict(set)  # TODO example
    statistics: dict  # {entity: absolute_frequency}, e.g. {'anarchism': 1234, 'foo': 0, ...}

    def __init__(self, freenode_json, wiki_xml, links_db, matches_db, commit_frequency, in_memory, limit_docs):
        self.freenode_to_wikidata_json = freenode_json
        self.wiki_xml = wiki_xml
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

        if self.in_memory:
            self.__run_in_memory()
        else:
            self.__run_on_disk()

    def __run_on_disk(self):
        with sqlite3.connect(self.matches_db) as matches_conn:
            create_pages_table(matches_conn)
            create_matches_table(matches_conn)
            self.__process_wikipedia(matches_conn)
            print('{} | DONE'.format(datetime.now().strftime('%H:%M:%S')))

    def __run_in_memory(self):
        with sqlite3.connect(':memory:') as memory_conn:
            create_pages_table(memory_conn)
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
                dumpr.BatchReader(self.wiki_xml) as reader:

            for doc_count, dumpr_doc in enumerate(reader.docs):
                if self.limit and doc_count > self.limit:
                    break

                if self.commit_frequency and doc_count % self.commit_frequency == 0:
                    print('{} | COMMIT'.format(datetime.now().strftime('%H:%M:%S')))
                    matches_conn.commit()
                    # self.plot_statistics()

                if dumpr_doc.content is None:
                    continue

                self.process_page(dumpr_doc, matches_conn, links_conn, doc_count)

    def process_page(self, dumpr_doc, matches_conn, links_conn, page_count):
        current_page = dumpr_doc.meta['title']

        #
        # Store doc in docs table
        #

        insert_page(matches_conn, Page(current_page, dumpr_doc.content))

        #
        # spaCy
        #

        spacy_doc = self.nlp.make_doc(dumpr_doc.content)
        matches = self.matcher(spacy_doc)

        #
        # Query neighbor pages
        #

        pages_linked_from_current_page = select_pages_linked_from(links_conn, current_page)
        pages_linking_to_current_page = select_pages_linking_to(links_conn, current_page)

        neighbor_pages = pages_linking_to_current_page | {current_page} | pages_linked_from_current_page

        #
        # Process all Freenode entities & save if in neighbor docs
        #

        match_count = 0
        for match_id, start, end in matches:
            entity_span = spacy_doc[start:end]
            entity_labels = entity_span.text

            if not self.entities[entity_labels]:
                continue

            entity_page_title = list(self.entities[entity_labels])[0][1]
            if entity_page_title not in neighbor_pages:
                continue

            mid = list(self.entities[entity_labels])[0][0]

            context_start = max(entity_span.start_char - 20, 0)
            context_end = min(entity_span.end_char + 20, len(dumpr_doc.content))
            context = dumpr_doc.content[context_start:context_end]

            match = Match(mid, entity_labels, current_page, entity_span.start_char, entity_span.end_char, context)
            insert_match(matches_conn, match)

            match_count += 1
            self.statistics[entity_labels] += 1

        print('{} | {:,} Docs | {} | {:,} neighbors | {:,} matches'.format(
            datetime.now().strftime("%H:%M:%S"), page_count, current_page, len(neighbor_pages), match_count))
