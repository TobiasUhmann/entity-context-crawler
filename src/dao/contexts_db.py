from dataclasses import dataclass
from sqlite3 import Connection
from typing import List


@dataclass
class Context:
    entity: int
    entity_label: str
    context: str
    masked_context: str


def create_contexts_table(conn: Connection):
    sql = '''
        CREATE TABLE contexts (
            id INT PRIMARY KEY AUTOINCREMENT,
            
            entity INT,
            entity_label TEXT,
            context TEXT,
            masked_context TEXT
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


def insert_context(conn: Connection, context: Context):
    sql = '''
        INSERT INTO contexts (entity, entity_label, context, masked_context)
        VALUES (?, ?, ?, ?)
    '''

    cursor = conn.cursor()
    cursor.execute(sql, (context.entity, context.entity_label, context.context, context.masked_context))
    cursor.close()


def insert_contexts(conn: Connection, contexts: List[Context]):
    sql = '''
        INSERT INTO contexts (entity, entity_label, context, masked_context)
        VALUES (?, ?, ?, ?)
    '''

    cursor = conn.cursor()
    rows = [(c.entity, c.entity_label, c.context, c.masked_context) for c in contexts]
    cursor.executemany(sql, rows)
    cursor.close()


def select_contexts(conn: Connection, entity: int, limit: int = None) -> List[Context]:
    sql = '''
        SELECT entity, entity_label, context, masked_context
        FROM contexts
        WHERE entity = ?
    '''

    cursor = conn.cursor()

    if limit:
        sql += 'LIMIT ?'
        cursor.execute(sql, (entity, limit))
    else:
        cursor.execute(sql, (entity,))

    rows = cursor.fetchall()
    cursor.close()

    return [Context(row[0], row[1], row[2], row[3]) for row in rows]
