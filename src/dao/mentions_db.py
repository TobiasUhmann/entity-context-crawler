from dataclasses import dataclass
from sqlite3 import Connection
from typing import List


@dataclass
class Mention:
    mid: str
    entity: str
    mention: str
    page: str


def create_mentions_table(conn: Connection):
    sql = '''
        CREATE TABLE mentions (
            mid TEXT,       -- Freebase MID of the entity that is referred, e.g. '/m/02_286'
            entity TEXT,    -- Label of the entity that is referred, e.g. 'New York City'      
            mention TEXT,   -- Text by which the entity is referred, e.g. 'New York'
            page TEXT       -- Wikipedia page that contains the mention, 
                            --     e.g. 'List of United States cities by population'
        )
    '''

    cursor = conn.cursor()
    cursor.execute(sql)
    cursor.close()


def select_mentions(conn: Connection, mid: str) -> List[str]:
    sql = '''
        SELECT mid, entity, mention, page
        FROM mentions
        WHERE mid = ?
    '''

    cursor = conn.cursor()
    cursor.execute(sql, (mid,))
    rows = cursor.fetchall()
    cursor.close()

    return [row for row in rows]


def insert_mentions(conn: Connection, mentions: List[Mention]):
    sql = '''
        INSERT OR IGNORE INTO mentions (mid, entity, mention, page)
        VALUES (?, ?, ?, ?)
    '''

    cursor = conn.cursor()
    rows = [(m.mid, m.entity, m.mention, m.page) for m in mentions]
    cursor.executemany(sql, rows)
    cursor.close()
