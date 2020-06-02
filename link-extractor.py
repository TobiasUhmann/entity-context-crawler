import sqlite3
import wikitextparser as wtp

from collections import defaultdict
from datetime import datetime
from wikipedia import Wikipedia

WIKIPEDIA_XML = 'enwiki-latest-pages-articles.xml'
LINKS_SQLITE_DB = 'links.db'


def create_links_db(conn):
    sql_create_table = '''
        CREATE TABLE links (
            from_doc int,      -- lowercase Wikipedia doc title
            to_doc int         -- lowercase Wikipedia doc title
        )
    '''

    sql_create_index_1 = '''
        CREATE INDEX idx_from_doc 
        ON links (from_doc)
    '''

    sql_create_index_2 = '''
        CREATE INDEX idx_to_doc
        ON links (to_doc)
    '''

    cursor = conn.cursor()
    cursor.execute(sql_create_table)
    cursor.execute(sql_create_index_1)
    cursor.execute(sql_create_index_2)
    cursor.close()


def insert_links(conn, links):
    sql = '''
        INSERT INTO links (from_doc, to_doc)
        VALUES(?, ?)
    '''

    cursor = conn.cursor()
    cursor.executemany(sql, links)
    cursor.close()


def main():
    link_count = 0
    missing_text_count = 0

    redirects = defaultdict(set)
    redirect_count = 0

    with open(WIKIPEDIA_XML, 'rb') as xml, \
            sqlite3.connect(LINKS_SQLITE_DB) as conn:
        
        create_links_db(conn)

        for page_count, page in enumerate(Wikipedia(xml, tag='page')):
            if page_count % 1000 == 0:
                conn.commit()
                print('{} | {:,} <page>s | {:,} redirects | {:,} links | {:,} missing text'.format(
                    datetime.now().strftime("%H:%M:%S"), page_count, redirect_count, link_count, missing_text_count))

            from_doc = hash(page['title'][0].lower())

            if page['redirect']:
                to_doc = hash(page['redirect'][0].lower())
                redirects[from_doc].add(to_doc)
                redirect_count += 1

            elif page['text']:
                links = wtp.parse(page['text'][0]).wikilinks
                inserts = [(from_doc, hash(link.title.lower())) for link in links]
                insert_links(conn, inserts)
                link_count += len(inserts)

            else:
                missing_text_count += 1


if __name__ == '__main__':
    main()
