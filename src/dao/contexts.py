from sqlite3 import Connection
from typing import List, Tuple


def create_contexts_table(conn: Connection):
    sql = '''
        CREATE TABLE contexts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            
            entity INTEGER,
            context TEXT,
            
            entity_label TEXT
        )
    '''

    cursor = conn.cursor()
    cursor.execute(sql)
    cursor.close()


def select_distinct_entities(conn: Connection) -> List[int]:
    sql = '''
        SELECT DISTINCT entity
        FROM contexts
    '''

    cursor = conn.cursor()
    cursor.execute(sql)
    rows = cursor.fetchall()
    cursor.close()

    return [row[0] for row in rows]


def insert_context(conn: Connection, entity: int, context: str, entity_label: str):
    sql = '''
        INSERT INTO contexts (entity, context, entity_label)
        VALUES (?, ?, ?)
    '''

    cursor = conn.cursor()
    cursor.execute(sql, (entity, context, entity_label))
    cursor.close()


def insert_contexts(conn, contexts: List[Tuple[int, str, str]]):
    """
    :param contexts: [(entity, context, entity_label)]
    """

    sql = '''
        INSERT INTO contexts (entity, context, entity_label)
        VALUES (?, ?, ?)
    '''

    cursor = conn.cursor()
    cursor.executemany(sql, contexts)
    cursor.close()


def select_contexts(conn: Connection, entity: int, limit: int = None) -> List[str]:
    sql = '''
        SELECT context
        FROM contexts
        WHERE entity = ?
        ORDER BY RANDOM()
    '''

    cursor = conn.cursor()

    if limit:
        sql += 'LIMIT ?'
        cursor.execute(sql, (entity, limit))
    else:
        cursor.execute(sql, (entity,))

    rows = cursor.fetchall()
    cursor.close()

    return [row[0] for row in rows]
