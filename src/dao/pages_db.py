from dataclasses import dataclass
from sqlite3 import Connection
from typing import Optional


#
# Raw Pages
#

@dataclass
class RawPage:
    title: str
    markup: str


def create_raw_pages_table(conn: Connection):
    create_table_sql = '''
        CREATE TABLE raw_pages (
            title TEXT,
            markup TEXT
        )
    '''

    create_title_index_sql = '''
        CREATE INDEX raw_pages_title_index 
        ON raw_pages (title)
    '''

    cursor = conn.cursor()
    cursor.execute(create_table_sql)
    cursor.execute(create_title_index_sql)
    cursor.close()


def select_raw_page(conn: Connection, title: str) -> Optional[RawPage]:
    sql = '''
        SELECT title, markup
        FROM pages
        WHERE title = ?
    '''

    cursor = conn.cursor()
    cursor.execute(sql, (title,))
    row = cursor.fetchone()
    cursor.close()

    return None if row is None else RawPage(row[0], row[1])


def insert_raw_page(conn: Connection, raw_page: RawPage):
    sql = '''
        INSERT INTO raw_pages (title, markup)
        VALUES (?, ?)
    '''

    cursor = conn.cursor()
    cursor.execute(sql, (raw_page.title, raw_page.markup))
    cursor.close()


#
# Text Pages
#

@dataclass
class TextPage:
    title: str
    text: str


def create_text_pages_table(conn: Connection):
    create_table_sql = '''
        CREATE TABLE text_pages (
            title TEXT,
            text TEXT
        )
    '''

    create_title_index_sql = '''
        CREATE INDEX text_pages_title_index 
        ON text_pages (title)
    '''

    cursor = conn.cursor()
    cursor.execute(create_table_sql)
    cursor.execute(create_title_index_sql)
    cursor.close()


def select_text_page(conn: Connection, title: str) -> Optional[TextPage]:
    sql = '''
        SELECT title, text
        FROM text_pages
        WHERE title = ?
    '''

    cursor = conn.cursor()
    cursor.execute(sql, (title,))
    row = cursor.fetchone()
    cursor.close()

    return None if row is None else TextPage(row[0], row[1])


def insert_text_page(conn: Connection, text_page: TextPage):
    sql = '''
        INSERT INTO text_pages (title, text)
        VALUES (?, ?)
    '''

    cursor = conn.cursor()
    cursor.execute(sql, (text_page.title, text_page.text))
    cursor.close()
