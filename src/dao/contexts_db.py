from dataclasses import dataclass
from sqlite3 import Connection
from typing import List, Optional


@dataclass
class Context:
    entity: int
    entity_label: str
    mention: Optional[str]
    page_title: Optional[str]
    context: Optional[str]
    masked_context: str


def create_contexts_table(conn: Connection):
    create_table_sql = '''
        CREATE TABLE contexts (
            entity INT,
            entity_label TEXT,
            mention TEXT,
            page_title TEXT,
            context TEXT,
            masked_context TEXT
        )
    '''

    create_entity_index_sql = '''
        CREATE INDEX entity_index
        ON contexts(entity)
    '''

    cursor = conn.cursor()
    cursor.execute(create_table_sql)
    cursor.execute(create_entity_index_sql)
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
        INSERT INTO contexts (entity, entity_label, mention, page_title, context, masked_context)
        VALUES (?, ?, ?, ?, ?, ?)
    '''

    cursor = conn.cursor()
    cursor.execute(sql, (context.entity, context.entity_label, context.mention, context.page_title, context.context,
                         context.masked_context))
    cursor.close()


def insert_contexts(conn: Connection, contexts: List[Context]):
    sql = '''
        INSERT INTO contexts (entity, entity_label, mention, page_title, context, masked_context)
        VALUES (?, ?, ?, ?, ?, ?)
    '''

    cursor = conn.cursor()
    rows = [(c.entity, c.entity_label, c.mention, c.page_title, c.context, c.masked_context) for c in contexts]
    cursor.executemany(sql, rows)
    cursor.close()


def select_contexts(conn: Connection, entity: int, limit: int = None) -> List[Context]:
    sql = '''
        SELECT entity, entity_label, mention, page_title, context, masked_context
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

    return [Context(row[0], row[1], row[2], row[3], row[4], row[5]) for row in rows]
