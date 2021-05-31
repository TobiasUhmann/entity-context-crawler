from typing import Dict


def load_mid2rid(path: str) -> Dict[str, int]:
    """
    :param path: path to mid2rid TXT
    :return: dict: Freebase MID -> ryn ID
    """

    mid2rid = dict()

    with open(path, encoding='utf-8') as fh:
        next(fh)
        for line in fh.readlines():
            mid, rid = line.split()
            mid2rid[mid] = int(rid)

    return mid2rid
