from typing import Dict


def load_mid2ryn(path: str) -> Dict[str, int]:
    """
    :param path: path to mid2ryn TXT
    :return: dict: Freebase MID -> ryn ID
    """

    mid2ryn = dict()

    with open(path) as fh:
        next(fh)
        for line in fh.readlines():
            mid, ryn = line.split('\t')
            mid2ryn[mid] = ryn

    return mid2ryn
