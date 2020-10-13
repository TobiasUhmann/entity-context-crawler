from dataclasses import dataclass
from sqlite3 import Connection
from typing import List


#
# Pages
#

@dataclass
class Page:
    title: str
    text: str


def create_pages_table(conn: Connection):
    sql = '''
        CREATE TABLE pages (
            title TEXT,
            text TEXT,
            
            PRIMARY KEY (title)
        )
    '''

    cursor = conn.cursor()
    cursor.execute(sql)
    cursor.close()


def insert_page(conn: Connection, page: Page):
    sql = '''
        INSERT INTO pages (title, text)
        VALUES (?, ?)
    '''

    cursor = conn.cursor()
    cursor.execute(sql, (page.title, page.text))
    cursor.close()


#
# Matches
#

@dataclass
class Match:
    mid: str
    entity_label: str
    mention: str
    page: str
    start_char: int
    end_char: int
    context: str


def create_matches_table(conn: Connection):
    sql = '''
        CREATE TABLE matches (
            mid TEXT,           -- MID = Freebase ID, e.g. '/m/012s1d'
            entity_label TEXT,  -- Wikidata label for MID, not unique, e.g. 'Spider-Man'
            mention TEXT,       -- Matched mention in Wikipedia, e.g. 'Spidey'
            page TEXT,          -- Wikipedia page title, unique, e.g. 'Spider-Man (2002 film)'
            start_char INT,     -- Start char position of entity match within document
            end_char INT,       -- End char position (exclusive) of entity match within document
            context TEXT,       -- Text around match, e.g. 'Spider-Man is a 2002 American...', for debugging

            FOREIGN KEY (page) REFERENCES pages (title),
            PRIMARY KEY (mid, page, start_char, mention)
        )
    '''

    cursor = conn.cursor()
    cursor.execute(sql)
    cursor.close()


def insert_match(conn: Connection, match: Match):
    sql = '''
        INSERT INTO matches (mid, entity_label, mention, page, start_char, end_char, context)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    '''

    cursor = conn.cursor()
    row = (match.mid, match.entity_label, match.mention, match.page, match.start_char, match.end_char, match.context)
    cursor.execute(sql, row)
    cursor.close()


#
# Mentions
#

@dataclass
class Mention:
    mid: str
    entity_label: str
    mention: str


def create_mentions_table(conn: Connection):
    sql = '''
        CREATE TABLE mentions (
            mid TEXT,
            entity_label TEXT,
            mention TEXT,

            PRIMARY KEY (mid)
        )
    '''

    cursor = conn.cursor()
    cursor.execute(sql)
    cursor.close()


def insert_or_ignore_mention(conn: Connection, mention: Mention):
    sql = '''
        INSERT OR IGNORE INTO mentions (mid, entity_label, mention)
        VALUES (?, ?, ?)
    '''

    cursor = conn.cursor()
    cursor.execute(sql, (mention.mid, mention.entity_label, mention.mention))
    cursor.close()


def select_distinct_mentions(conn: Connection, mid: str):
    sql = '''
        SELECT DISTINCT mention
        FROM mentions
        WHERE mid = ?
    '''

    cursor = conn.cursor()
    cursor.execute(sql, (mid,))
    rows = cursor.fetchall()
    cursor.close()

    return [row[0] for row in rows]


#
# Pages x Matches
#

def select_contexts(conn: Connection, mid: str, size: int) -> List[str]:
    """
    :param size: maximum chars before and after match, respectively
    """

    sql = '''
        -- SELECT context = [max <size> chars] + [entity] + [max <size> chars]

        SELECT SUBSTR(text,
                      MAX(start_char + 1 - ?, 1), 
                      MIN((start_char + 1 - MAX(start_char + 1 - ?, 1)) + (end_char - start_char) + ?, length(text)))
        FROM pages INNER JOIN matches ON pages.title = matches.page
        WHERE mid = ?
    '''

    cursor = conn.cursor()
    cursor.execute(sql, (size, size, size, mid))
    rows = cursor.fetchall()
    cursor.close()

    return [row[0] for row in rows]
