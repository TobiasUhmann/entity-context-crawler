from typing import Dict


def load_qid_to_rid(path: str) -> Dict[str, int]:
    """
    :param path: path to QID-to-RID TXT
    :return: dict: QID -> RID
    """

    qid_to_rid = dict()

    with open(path) as f:
        next(f)  # Skip first line

        for line in f.readlines():
            qid, rid = line.split(' ')
            qid_to_rid[qid] = int(rid)

    return qid_to_rid
