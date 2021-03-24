from dataclasses import dataclass
from sqlite3 import Connection
from typing import List, Tuple


#
# Pages
#

@dataclass
class PageStats:
    link_count: int
    entity_link_count: int
    mention_count: int
    unique_mention_count: int
    text_len: int
    clean_text_len: int
    match_count: int


@dataclass
class Page:
    title: str
    text: str
    stats: PageStats


def version_matches_db(conn: Connection):
    with conn:
        conn.execute('PRAGMA user_version = 6')


def create_pages_table(conn: Connection):
    sql = '''
        CREATE TABLE pages (
            id                      INT,
            
            title                   TEXT,
            text                    TEXT,
            
            link_count              INT,
            entity_link_count       INT,
            mention_count           INT,
            unique_mention_count    INT,
            text_len                INT,
            clean_text_len          INT,
            match_count             INT,
            
            PRIMARY KEY (id)
        )
    '''

    cursor = conn.cursor()
    cursor.execute(sql)
    cursor.close()


def insert_page(conn: Connection, page: Page):
    sql = '''
        INSERT OR IGNORE INTO pages (title, text, link_count, entity_link_count, mention_count, unique_mention_count,
                                     text_len, clean_text_len, match_count)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    '''

    cursor = conn.cursor()
    cursor.execute(sql, (page.title, page.text, page.stats.link_count, page.stats.entity_link_count,
                         page.stats.mention_count, page.stats.unique_mention_count, page.stats.text_len,
                         page.stats.clean_text_len, page.stats.match_count))
    cursor.close()


#
# Matches
#

@dataclass
class Match:
    oid: str
    entity_label: str
    mention: str
    page: str
    start_char: int
    end_char: int
    context: str


def create_matches_table(conn: Connection):
    sql = '''
        CREATE TABLE matches (
            id              INT,
            
            page            TEXT,  -- Wikipedia page title, unique, e.g. 'Spider-Man (2002 film)'

            oid             TEXT,  -- OID = Wikidata ID, e.g. 'Q1234'
            entity_label    TEXT,  -- Wikidata label for OID, not unique, e.g. 'Spider-Man'
            mention         TEXT,  -- Matched mention in Wikipedia, e.g. 'Spidey'
            start_char      INT,   -- Start char position of entity match within document
            end_char        INT,   -- End char position (exclusive) of entity match within document
            context         TEXT,  -- Text around match, e.g. 'Spider-Man is a 2002 American...', for debugging

            PRIMARY KEY (id),
            FOREIGN KEY (page) REFERENCES pages(title)
        )
    '''

    cursor = conn.cursor()
    cursor.execute(sql)
    cursor.close()


def insert_match(conn: Connection, match: Match):
    sql = '''
        INSERT INTO matches (oid, entity_label, mention, page, start_char, end_char, context)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    '''

    cursor = conn.cursor()
    row = (match.oid, match.entity_label, match.mention, match.page, match.start_char, match.end_char, match.context)
    cursor.execute(sql, row)
    cursor.close()


#
# Mentions
#

@dataclass
class Mention:
    oid: str
    entity_label: str
    mention: str


def create_mentions_table(conn: Connection):
    create_table_sql = '''
        CREATE TABLE mentions (
            id              INT,
            
            oid             TEXT,
            mention         TEXT,
            entity_label    TEXT,

            PRIMARY KEY (id),
            UNIQUE (oid, mention)
        )
    '''

    create_oid_index_sql = '''
        CREATE INDEX mentions_oid_index
        ON mentions(oid)
    '''

    cursor = conn.cursor()
    cursor.execute(create_table_sql)
    cursor.execute(create_oid_index_sql)
    cursor.close()


def insert_or_ignore_mention(conn: Connection, mention: Mention):
    sql = '''
        INSERT OR IGNORE INTO mentions (oid, entity_label, mention)
        VALUES (?, ?, ?)
    '''

    cursor = conn.cursor()
    cursor.execute(sql, (mention.oid, mention.entity_label, mention.mention))
    cursor.close()


def select_entity_mentions(conn: Connection, oid: str) -> List[str]:
    sql = '''
        SELECT DISTINCT mention
        FROM mentions
        WHERE oid = ?
    '''

    cursor = conn.cursor()
    cursor.execute(sql, (oid,))
    rows = cursor.fetchall()
    cursor.close()

    return [row[0] for row in rows]


#
# Pages x Matches
#

def select_contexts(conn: Connection, oid: str, size: int) -> List[Tuple[str, str, str]]:
    """
    :param size: maximum chars before and after match, respectively

    :return [(context, page_title, mention)]
    """

    sql = '''
        -- SELECT context = [max <size> chars] + [entity] + [max <size> chars]

        SELECT SUBSTR(text,
                      MAX(start_char + 1 - ?, 1), 
                      MIN((start_char + 1 - MAX(start_char + 1 - ?, 1)) + (end_char - start_char) + ?, length(text))),
               pages.title,
               matches.mention
        FROM pages INNER JOIN matches ON pages.title = matches.page
        WHERE oid = ?
    '''

    cursor = conn.cursor()
    cursor.execute(sql, (size, size, size, oid))
    rows = cursor.fetchall()
    cursor.close()

    return [(row[0], row[1], row[2]) for row in rows]
