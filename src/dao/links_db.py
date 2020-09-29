from dataclasses import dataclass
from sqlite3 import Connection
from typing import List, Set


@dataclass
class Link:
    from_page: str
    to_page: str


def create_links_table(conn: Connection):
    create_table = '''
        CREATE TABLE links (
            from_page TEXT,
            to_page TEXT
        )
    '''

    create_from_page_index = '''
        CREATE INDEX index_from_page 
        ON links (from_page)
    '''

    create_to_page_index = '''
        CREATE INDEX index_to_page
        ON links (to_page)
    '''

    cursor = conn.cursor()
    cursor.execute(create_table)
    cursor.execute(create_from_page_index)
    cursor.execute(create_to_page_index)
    cursor.close()


def insert_links(conn: Connection, links: List[Link]):
    sql = '''
        INSERT INTO links (from_page, to_page)
        VALUES (?, ?)
    '''

    cursor = conn.cursor()
    cursor.executemany(sql, [(link.from_page, link.to_page) for link in links])
    cursor.close()


def select_pages_linked_from(conn: Connection, from_page: str) -> Set[str]:
    sql = '''
        SELECT to_page
        FROM links
        WHERE from_page = ?
    '''

    cursor = conn.cursor()
    cursor.execute(sql, (from_page,))
    rows = cursor.fetchall()
    cursor.close()

    return {row[0] for row in rows}


def select_pages_linking_to(conn: Connection, to_page: str) -> Set[str]:
    sql = '''
            SELECT from_page
            FROM links
            WHERE to_page = ?
        '''

    cursor = conn.cursor()
    cursor.execute(sql, (to_page,))
    rows = cursor.fetchall()
    cursor.close()

    return {row[0] for row in rows}
