def select_distinct_entities(conn):
    sql = '''
        SELECT DISTINCT entity
        FROM matches
    '''

    cursor = conn.cursor()
    cursor.execute(sql)
    rows = cursor.fetchall()
    cursor.close()

    return [row[0] for row in rows]


def select_contexts(conn, entity, size):
    sql = '''
        -- SELECT context = [max <size> chars] + [entity] + [max <size> chars]

        SELECT SUBSTR(content,
                      MAX(start_char + 1 - ?, 1), 
                      MIN((start_char + 1 - MAX(start_char + 1 - ?, 1)) + (end_char - start_char) + ?, length(content)))
        FROM docs INNER JOIN matches ON docs.title = matches.doc
        WHERE entity = ?
    '''

    cursor = conn.cursor()
    cursor.execute(sql, (size, size, size, entity))
    rows = cursor.fetchall()
    cursor.close()

    return [row[0] for row in rows]
