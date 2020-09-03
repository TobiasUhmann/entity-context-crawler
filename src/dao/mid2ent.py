from typing import Dict


def load_mid2ent(path: str) -> Dict[str, int]:
    """
    :param path: path to OpenKE entity2id.txt
    :return: dict: Freebase MID -> OpenKE ID
    """

    mid2ent = dict()

    with open(path) as fh:
        next(fh)
        for line in fh.readlines():
            mid, ent = line.split('\t')
            mid2ent[mid] = ent

    return mid2ent
