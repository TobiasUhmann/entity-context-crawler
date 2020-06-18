import argparse
import sqlite3

from collections import defaultdict, Counter
from elasticsearch import Elasticsearch
from os.path import isfile

from dao.test_contexts import select_distinct_entities, select_contexts


def main():
    #
    # Parse args
    #

    parser = argparse.ArgumentParser(
        description='Query Elasticsearch index for test contexts',
        formatter_class=lambda prog: argparse.MetavarTypeHelpFormatter(prog, max_help_position=50, width=120))

    parser.add_argument('index_name', metavar='index-name', type=str,
                        help='name of input Elasticsearch index')

    parser.add_argument('test contexts_db', metavar='test-contexts-db', type=str,
                        help='path to input test contexts DB')

    default_limit_contexts = 100
    parser.add_argument('--limit-contexts', dest='limit_contexts', type=int, default=default_limit_contexts,
                        help='only process the first ... contexts for each entity'
                             ' (default: {})'.format(default_limit_contexts))

    default_limit_entities = 10
    parser.add_argument('--limit-entities', dest='limit_entities', type=int, default=default_limit_entities,
                        help='only process the first ... entities'
                             ' (default: {})'.format(default_limit_entities))

    default_top_hits = 10
    parser.add_argument('--top-hits', dest='top_hits', type=int, default=default_top_hits,
                        help='evaluate the top ... hits for each query'
                             ' (default: {})'.format(default_top_hits))

    args = parser.parse_args()

    #
    # Print applied config
    #

    print('Applied config:')
    print('    {:20} {}'.format('Index name', args.index_name))
    print('    {:20} {}'.format('Test contexts DB', args.test_contexts))
    print()
    print('    {:20} {}'.format('Limit contexts', args.limit_contexts))
    print('    {:20} {}'.format('Limit entities', args.limit_entities))
    print('    {:20} {}'.format('Top hits', args.limit_entities))
    print()

    #
    # Check for input/output files
    #

    if not isfile(args.test_contexts_db):
        print('Test contexts DB not found')
        exit()

    es = Elasticsearch()
    if not es.indices.exists(index=args.index_name):
        print('Elasticsearch index not found')
        exit()

    #
    # Run program
    #

    query_contexts(es, args.index_name, args.test_contexts_db, args.limit_contexts, args.limit_entities, args.top_hits)


def query_contexts(es, index_name, test_contexts_db, limit_contexts, limit_entities, top_hits):
    with sqlite3.connect(test_contexts_db) as test_contexts_conn:
        stats = defaultdict(Counter)

        entities = select_distinct_entities(test_contexts_conn, limit_entities)

        for entity in entities:
            test_contexts = select_contexts(test_contexts_conn, limit_contexts)
            for test_context in test_contexts:
                print(' {:5}  {:24}  {}'.format('QUERY', entity, repr(test_context[:100])))
                print(100 * '-')

                res = es.search(index=index_name, body={'query': {'match': {'context': test_context}}})

                hits = res['hits']['hits']
                for hit in hits[:top_hits]:
                    score = hit['_score']
                    hit_entity = hit['_source']['entity']
                    concat = repr(hit['_source']['context'][:100])
                    print(' {:5.1f}  {:24}  {}'.format(score, hit_entity, concat))
                    stats[entity][hit_entity] += 1

                print()


#
#
#

if __name__ == '__main__':
    main()
