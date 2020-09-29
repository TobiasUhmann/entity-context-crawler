from sqlite3 import Connection


def create_links_table(conn: Connection):
    sql_create_table = '''
        CREATE TABLE links (
            from_doc int,      -- hashed lowercase Wikipedia doc title
            to_doc int         -- hashed lowercase Wikipedia doc title
        )
    '''

    sql_create_index_1 = '''
        CREATE INDEX idx_from_doc 
        ON links (from_doc)
    '''

    sql_create_index_2 = '''
        CREATE INDEX idx_to_doc
        ON links (to_doc)
    '''

    cursor = conn.cursor()
    cursor.execute(sql_create_table)
    cursor.execute(sql_create_index_1)
    cursor.execute(sql_create_index_2)
    cursor.close()


def insert_links(conn, links):
    sql = '''
        INSERT INTO links (from_doc, to_doc)
        VALUES(?, ?)
    '''

    cursor = conn.cursor()
    cursor.executemany(sql, links)
    cursor.close()
