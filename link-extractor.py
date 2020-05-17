import sqlite3
from datetime import datetime

import wikitextparser as wtp

from wikipedia import Wikipedia

WIKIPEDIA_XML = 'enwiki-latest-pages-articles.xml'
LINKS_SQLITE_DB = 'links.db'


def create_links_db(conn):
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE links (
            from_doc text,      -- lowercase Wikipedia doc title
            to_doc text         -- lowercase Wikipedia doc title
        );
    ''')

    cursor.execute('''
        CREATE INDEX idx_from_doc 
        ON links (from_doc);
    ''')

    cursor.execute('''
        CREATE INDEX idx_to_doc
        ON links (to_doc);
    ''')

    cursor.close()


def insert_link(conn, from_doc, to_doc):
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO links (from_doc, to_doc)
        VALUES(?, ?)
    ''', (from_doc, to_doc))

    cursor.close()


def main():
    link_count = 0
    missing_text = 0

    with open(WIKIPEDIA_XML, 'rb') as xml, sqlite3.connect(LINKS_SQLITE_DB) as conn:
        create_links_db(conn)

        for page_count, page in enumerate(Wikipedia(xml, tag='page')):
            if page_count % 1000 == 0:
                conn.commit()
                print('{} | {:,} <page>s | {:,} links | {:,} missing text'.format(
                    datetime.now().strftime("%H:%M:%S"), page_count, link_count, missing_text))

            from_doc = page['title'][0].lower()

            # if page['redirect']:
            #     target_doc = hash(page['redirect'][0].lower())

            if page['text']:
                links = wtp.parse(page['text'][0]).wikilinks
                for link in links:
                    to_doc = link.title.lower()
                    insert_link(conn, from_doc, to_doc)
                    link_count += 1
            else:
                missing_text += 1


if __name__ == '__main__':
    main()
