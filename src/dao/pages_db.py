from dataclasses import dataclass
from sqlite3 import Connection


@dataclass
class Page:
    title: str
    content: str


def create_pages_table(conn: Connection):
    sql = '''
        CREATE TABLE pages (
            title TEXT,
            content TEXT,

            PRIMARY KEY (title)
        )
    '''

    cursor = conn.cursor()
    cursor.execute(sql)
    cursor.close()


def select_page(conn: Connection, title: str) -> Page:
    sql = '''
        SELECT title, content
        FROM pages
        WHERE title = ?
    '''

    cursor = conn.cursor()
    cursor.execute(sql, (title,))
    row = cursor.fetchone()
    cursor.close()

    return Page(row[0], row[1])


def insert_page(conn: Connection, page: Page):
    sql = '''
        INSERT INTO pages (title, content)
        VALUES (?, ?)
    '''

    cursor = conn.cursor()
    cursor.execute(sql, (page.title, page.content))
    cursor.close()
