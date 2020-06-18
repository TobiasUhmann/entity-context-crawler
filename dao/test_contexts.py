def create_contexts_table(conn):
    sql = '''
        CREATE TABLE contexts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entity TEXT,
            context TEXT
        )
    '''


def insert_context(contexts_conn, entity, context):
    sql = '''
        INSERT INTO contexts (entity, context)
        VALUES (?, ?)
    '''

    cursor = contexts_conn.cursor()
    cursor.execute(sql, (entity, context))
    cursor.close()


def select_distinct_entities(conn, limit):
    sql = '''
        SELECT DISTINCT entity
        FROM contexts
        ORDER BY RANDOM()
    '''

    cursor = conn.cursor()

    if limit:
        sql += 'LIMIT ?'
        cursor.execute(sql, (limit,))
    else:
        cursor.execute(sql)

    rows = cursor.fetchall()
    cursor.close()

    return [row[0] for row in rows]


def select_contexts(conn, entity, limit):
    sql = '''
        SELECT entity, context
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

    return rows
