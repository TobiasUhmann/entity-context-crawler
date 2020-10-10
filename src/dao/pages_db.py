from dataclasses import dataclass
from sqlite3 import Connection
from typing import Optional


@dataclass
class Page:
    title: str
    markup: str


def create_pages_table(conn: Connection):
    sql = '''
        CREATE TABLE pages (
            title TEXT,
            markup TEXT,

            PRIMARY KEY (title)
        )
    '''

    cursor = conn.cursor()
    cursor.execute(sql)
    cursor.close()


def select_page(conn: Connection, title: str) -> Optional[Page]:
    sql = '''
        SELECT title, content
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
