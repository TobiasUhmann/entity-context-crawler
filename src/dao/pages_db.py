from dataclasses import dataclass
from sqlite3 import Connection
from typing import Optional, Set


@dataclass
class Page:
    title: str
    markup: str


def create_pages_table(conn: Connection):
    create_table_sql = '''
        CREATE TABLE pages (
            title TEXT,
            markup TEXT
        )
    '''

    create_title_index = '''
        CREATE INDEX index_title 
        ON pages (title)
    '''

    cursor = conn.cursor()
    cursor.execute(create_table_sql)
    cursor.execute(create_title_index)
    cursor.close()


def select_page(conn: Connection, title: str) -> Optional[Page]:
    sql = '''
        SELECT title, markup
        FROM pages
        WHERE title = ?
    '''

    cursor = conn.cursor()
    cursor.execute(sql, (title,))
    row = cursor.fetchone()
    cursor.close()

    return None if row is None else Page(row[0], row[1])


def insert_page(conn: Connection, page: Page):
    sql = '''
        INSERT INTO pages (title, markup)
        VALUES (?, ?)
    '''

    cursor = conn.cursor()
    cursor.execute(sql, (page.title, page.markup))
    cursor.close()
