import json
from typing import Dict


def load_oid_to_wikidata(wikidata_json: str) -> Dict[str, Dict[str, str]]:
    """
    :param wikidata_json: path to Wikidata JSON
    :return: dict: OID -> Wikidata
    """

    with open(wikidata_json, 'r') as f:
        oid_to_wikidata = json.load(f)

    return oid_to_wikidata
