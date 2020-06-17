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
