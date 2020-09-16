from sqlite3 import Connection
from typing import List, Tuple


def select_mids_with_labels(conn: Connection, limit: None) -> List[Tuple[str, str]]:
    """
    Select distinct MIDs with their associated labels

    :return: [(MID, entity label)]
    """

    sql = '''
        SELECT DISTINCT mid, entity
        FROM matches
    '''

    cursor = conn.cursor()

    if limit:
        sql += ' LIMIT ?'
        cursor.execute(sql, (limit,))
    else:
        cursor.execute(sql)

    rows = cursor.fetchall()
    cursor.close()

    return [(row[0], row[1]) for row in rows]


def select_contexts(conn: Connection, mid: str, size: int) -> List[str]:
    """
    :param size: maximum chars before and after match, respectively
    """

    sql = '''
        -- SELECT context = [max <size> chars] + [entity] + [max <size> chars]

        SELECT SUBSTR(content,
                      MAX(start_char + 1 - ?, 1), 
                      MIN((start_char + 1 - MAX(start_char + 1 - ?, 1)) + (end_char - start_char) + ?, length(content)))
        FROM docs INNER JOIN matches ON docs.title = matches.doc
        WHERE mid = ?
    '''

    cursor = conn.cursor()
    cursor.execute(sql, (size, size, size, mid))
    rows = cursor.fetchall()
    cursor.close()

    return [row[0] for row in rows]
