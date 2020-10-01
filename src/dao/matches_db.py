from dataclasses import dataclass
from sqlite3 import Connection
from typing import List, Tuple, Optional


@dataclass
class Page:
    title: str
    content: str


@dataclass
class Match:
    mid: str
    entity_label: str
    page: str
    start_char: int
    end_char: int
    context: str


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


def create_matches_table(conn: Connection):
    sql = '''
        CREATE TABLE matches (
            mid TEXT,           -- MID = Freebase ID, e.g. '/m/012s1d'
            entity_label TEXT,  -- Wikidata label for MID, not unique, e.g. 'Spider-Man'
            page TEXT,          -- Wikipedia page title, unique, e.g. 'Spider-Man (2002 film)'
            start_char INT,     -- Start char position of entity match within document
            end_char INT,       -- End char position (exclusive) of entity match within document
            context TEXT,       -- Text around match, e.g. 'Spider-Man is a 2002 American...', for debugging

            FOREIGN KEY (page) REFERENCES pages (title),
            PRIMARY KEY (mid, page, start_char, entity_label)
        )
    '''

    cursor = conn.cursor()
    cursor.execute(sql)
    cursor.close()


def insert_page(conn: Connection, page: Page):
    sql = '''
        INSERT INTO pages (title, content)
        VALUES (?, ?)
    '''

    cursor = conn.cursor()
    cursor.execute(sql, (page.title, page.content))
    cursor.close()


def insert_match(conn: Connection, match: Match):
    sql = '''
        INSERT INTO matches (mid, entity_label, page, start_char, end_char, context)
        VALUES (?, ?, ?, ?, ?, ?)
    '''

    cursor = conn.cursor()
    cursor.execute(sql, (match.mid, match.entity_label, match.page, match.start_char, match.end_char, match.context))
    cursor.close()


def select_mids_with_labels(conn: Connection, limit: int = None) -> List[Tuple[str, str]]:
    """
    Select distinct MIDs with their associated labels

    :return: [(MID, entity label)]
    """

    sql = '''
        SELECT DISTINCT mid, entity_label
        FROM matches
    '''

    cursor = conn.cursor()

    if limit:
        sql += ' LIMIT ?'
        cursor.execute(sql, (limit,))
    else:
        cursor.execute(sql)

    rows = cursor.fetchall()
    cursor.close()

    return [(row[0], row[1]) for row in rows]


def select_contexts(conn: Connection, mid: str, size: int) -> List[str]:
    """
    :param size: maximum chars before and after match, respectively
    """

    sql = '''
        -- SELECT context = [max <size> chars] + [entity] + [max <size> chars]

        SELECT SUBSTR(content,
                      MAX(start_char + 1 - ?, 1), 
                      MIN((start_char + 1 - MAX(start_char + 1 - ?, 1)) + (end_char - start_char) + ?, length(content)))
        FROM pages INNER JOIN matches ON LOWER(pages.title) = LOWER(matches.page)
        WHERE mid = ?
    '''

    cursor = conn.cursor()
    cursor.execute(sql, (size, size, size, mid))
    rows = cursor.fetchall()
    cursor.close()

    return [row[0] for row in rows]


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
