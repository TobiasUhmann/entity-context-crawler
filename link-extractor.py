import pickle
import sqlite3
import sys
from collections import defaultdict

import wikitextparser as wtp

from wikipedia import Wikipedia

FULL_WIKIPEDIA_DOCS_XML = 'enwiki-latest-pages-articles.xml'


def dd():
    return defaultdict(set)


def get_size(obj, seen=None):
    """Recursively finds size of objects"""
    size = sys.getsizeof(obj)
    if seen is None:
        seen = set()
    obj_id = id(obj)
    if obj_id in seen:
        return 0
    # Important mark as seen *before* entering recursion to gracefully handle
    # self-referential objects
    seen.add(obj_id)
    if isinstance(obj, dict):
        size += sum([get_size(v, seen) for v in obj.values()])
        size += sum([get_size(k, seen) for k in obj.keys()])
    elif hasattr(obj, '__dict__'):
        size += get_size(obj.__dict__, seen)
    elif hasattr(obj, '__iter__') and not isinstance(obj, (str, bytes, bytearray)):
        size += sum([get_size(i, seen) for i in obj])
    return size


def create_db(conn):
    sql_create_links = '''
        CREATE TABLE links (
            doc1 int,
            doc2 int
        );
    '''

    sql_create_index1 = '''
        CREATE INDEX index1 
        ON links (doc1);
    '''

    sql_create_index2 = '''
            CREATE INDEX index2
            ON links (doc2);
        '''

    cursor = conn.cursor()
    cursor.execute(sql_create_links)
    cursor.execute(sql_create_index1)
    cursor.execute(sql_create_index2)
    cursor.close()


def insert_db(conn, doc1, doc2):
    sql = '''
        INSERT INTO links(doc1, doc2)
        VALUES(?, ?)
    '''

    link = (doc1, doc2)

    cursor = conn.cursor()
    cursor.execute(sql, link)
    cursor.close()


if __name__ == '__main__':
    with open(FULL_WIKIPEDIA_DOCS_XML, 'rb') as xml:

        #
        # Build graph
        #

        link_count = 0
        with sqlite3.connect('links.db') as conn:
            create_db(conn)

            # links = defaultdict(dd)

            for count, page in enumerate(Wikipedia(xml, tag='page')):
                if count % 1000 == 0:
                    print(count, link_count)
                    # entries = 0
                    # for node in links:
                    #     entries += len(links[node]['links_to'])
                    #     entries += len(links[node]['linked_by'])
                    # print(len(links))
                    # print(entries)
                    # print(sys.getsizeof(links))
                    # print(get_size(links))
                    # print()

                if count == 10000:
                    break

                doc = page['title'][0].lower()

                if page['redirect']:
                    target_doc = hash(page['redirect'][0].lower())
                    # links[doc]['redirect'].add(target_doc)

                if page['text']:
                    wikilinks = wtp.parse(page['text'][0]).wikilinks
                    for wikilink in wikilinks:
                        linked_doc = wikilink.title.lower()
                        insert_db(conn, doc, linked_doc)
                        link_count += 1
                        # links[doc]['links_to'].add(linked_doc)
                        # links[linked_doc]['linked_by'].add(doc)

            #
            # Persist graph
            #

            # pickle.dump(links, open('links.p', 'wb'))
