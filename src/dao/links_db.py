from sqlite3 import Connection
from typing import List, Tuple


Link = Tuple[str, str]


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
        VALUES(?, ?)
    '''

    cursor = conn.cursor()
    cursor.executemany(sql, links)
    cursor.close()
