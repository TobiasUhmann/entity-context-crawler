from typing import Dict


def load_oid_to_rid(path: str) -> Dict[str, int]:
    """
    :param path: path to OID-to-RID TXT
    :return: dict: OID -> RID
    """

    oid_to_rid = dict()

    with open(path) as f:
        next(f)  # Skip first line

        for line in f.readlines():
            oid, rid = line.split(' ')
            oid_to_rid[oid] = int(rid)

    return oid_to_rid
