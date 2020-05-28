import sqlite3

from elasticsearch import Elasticsearch

MATCHES_DB = 'matches.db'


def select_entities(conn, limit):
    sql = '''
        SELECT DISTINCT entity
        FROM matches
        LIMIT ?
    '''

    cursor = conn.cursor()
    cursor.execute(sql, (limit,))
    rows = cursor.fetchall()
    cursor.close()

    return [row[0] for row in rows]


def select_contexts(conn, entity, limit):
    sql = '''
        SELECT context
        FROM matches
        WHERE entity = ?
        LIMIT ?
    '''

    cursor = conn.cursor()
    cursor.execute(sql, (entity, limit))
    rows = cursor.fetchall()
    cursor.close()

    return [row[0] for row in rows]


class EntityLinker:
    matches_db: str  # path/to/matches.db

    def __init__(self, matches_db):
        self.matches_db = matches_db

    def test(self):
        es = Elasticsearch()
        with sqlite3.connect(self.matches_db) as matches_conn:
            all_test_contexts = {}

            entities = select_entities(matches_conn, 100)
            for id, entity in enumerate(entities):
                contexts = select_contexts(matches_conn, entity, 100)
                cropped_contexts = [context[context.find(' ') + 1: context.rfind(' ')] for context in contexts]
                masked_contexts = [context.replace(entity, '') for context in cropped_contexts]

                train_contexts = masked_contexts[:int(0.7 * len(masked_contexts))]
                test_contexts = masked_contexts[int(0.7 * len(masked_contexts)):]
                all_test_contexts[entity] = test_contexts

                doc = {'entity': entity, 'context': ' '.join(train_contexts)}
                es.index(index="sentence-sampler-index", id=id, body=doc)
                es.indices.refresh(index="sentence-sampler-index")

            for entity in all_test_contexts:
                for test_context in all_test_contexts[entity]:
                    print(entity, '#', test_context)

                    res = es.search(index="sentence-sampler-index", body={"query": {"match": {'context': test_context}}})
                    print("Got %d Hits:" % res['hits']['total']['value'])
                    for hit in res['hits']['hits']:
                        print(hit['_score'], hit['_source'])
                    print()


def main():
    entity_linker = EntityLinker(MATCHES_DB)
    entity_linker.test()


if __name__ == '__main__':
    main()
