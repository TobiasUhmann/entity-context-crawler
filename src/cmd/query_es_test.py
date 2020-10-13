import os
import sqlite3

from argparse import ArgumentParser, Namespace
from collections import defaultdict, Counter
from elasticsearch import Elasticsearch
from os.path import isfile
from ryn.graphs.split import Dataset
from typing import List

from dao.contexts_db import select_contexts, select_distinct_entities


def add_parser_args(parser: ArgumentParser):
    """
    Add arguments to arg parser:
        es-index
        test-contexts-db
        --es-host
        --limit-contexts
        --limit-entities
        --top-hits
        --verbose
    """

    parser.add_argument('es_index', metavar='es-index',
                        help='Name of (input) Elasticsearch index')

    parser.add_argument('test_contexts_db', metavar='test-contexts-db',
                        help='Path to (input) test contexts DB')

    default_es_host = 'localhost:9200'
    parser.add_argument('--es-host', dest='es_host', metavar='STR', default=default_es_host,
                        help='Elasticsearch host (default: {})'.format(default_es_host))

    default_limit_contexts = None
    parser.add_argument('--limit-contexts', dest='limit_contexts', type=int, metavar='INT',
                        default=default_limit_contexts,
                        help='Process only first ... contexts for each entity'
                             ' (default: {})'.format(default_limit_contexts))

    default_limit_entities = None
    parser.add_argument('--limit-entities', dest='limit_entities', type=int, metavar='INT',
                        default=default_limit_entities,
                        help='Process only first ... entities'
                             ' (default: {})'.format(default_limit_entities))

    default_top_hits = 10
    parser.add_argument('--top-hits', dest='top_hits', type=int, metavar='INT', default=default_top_hits,
                        help='Evaluate only the top ... hits for each query'
                             ' (default: {})'.format(default_top_hits))

    parser.add_argument('--verbose', dest='verbose', action='store_true',
                        help='Print query contexts for each entity')


def run(args: Namespace):
    """
    - Print applied config
    - Check if files already exist
    - Run actual program
    """

    es_index = args.es_index
    test_contexts_db = args.test_contexts_db

    es_host = args.es_host
    limit_contexts = args.limit_contexts
    limit_entities = args.limit_entities
    top_hits = args.top_hits
    verbose = args.verbose

    python_hash_seed = os.getenv('PYTHONHASHSEED')

    #
    # Print applied config
    #

    print('Applied config:')
    print('    {:20} {}'.format('es-index', es_index))
    print('    {:20} {}'.format('test-contexts-db', test_contexts_db))
    print()
    print('    {:20} {}'.format('--es-host', es_host))
    print('    {:20} {}'.format('--limit-contexts', limit_contexts))
    print('    {:20} {}'.format('--limit-entities', limit_entities))
    print('    {:20} {}'.format('--top-hits', top_hits))
    print('    {:20} {}'.format('--verbose', verbose))
    print()
    print('    {:20} {}'.format('PYTHONHASHSEED', python_hash_seed))
    print()

    #
    # Check if files already exist
    #

    if not isfile(test_contexts_db):
        print('Test contexts DB not found')
        exit()

    es = Elasticsearch([es_host])
    if not es.indices.exists(index=es_index):
        print('Elasticsearch index not found')
        exit()

    #
    # Run actual program
    #

    _query_es_test(es, es_index, test_contexts_db, limit_contexts, limit_entities, top_hits, verbose)


def _query_es_test(es, index_name, test_contexts_db, limit_contexts, limit_entities, top_hits, verbose):
    with sqlite3.connect(test_contexts_db) as test_contexts_conn:
        stats = defaultdict(Counter)

        entities: List[int] = select_distinct_entities(test_contexts_conn)[:limit_entities]
        dataset = Dataset.load('')  # TODO
        id2ent = dataset.id2ent

        for entity in entities:
            entity_label = id2ent[entity]
            test_contexts = select_contexts(test_contexts_conn, entity, limit_contexts)
            test_contexts = [context.replace('#', '') for context in test_contexts]

            for test_context in test_contexts:

                if verbose:
                    print()
                    print(' {:5}  {:24}  {}'.format('QUERY', entity_label, repr(test_context[:100])))
                    print(100 * '-')

                res = es.search(index=index_name, body={'query': {'match': {'context': test_context}}})

                hits = res['hits']['hits']
                for hit in hits[:top_hits]:
                    score = hit['_score']
                    hit_entity = hit['_source']['entity_label']
                    concat = repr(hit['_source']['context'][:100])
                    stats[entity][hit_entity] += 1

                    if verbose:
                        print(' {:5.1f}  {:24}  {}'.format(score, hit_entity, concat))

        #
        # STATS
        #

        print()
        for entity, stat in stats.items():
            top_stat = stat.most_common(4)
            top_stat_count = sum(stat.values())

            print('{:3} / {:3} {:30} #   '.format(stat[entity], top_stat_count, id2ent[entity]), end='')
            for t in top_stat:
                print('{:3} {:30}'.format(t[1], t[0]), end='')
            print()
