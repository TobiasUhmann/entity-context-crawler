import json
from typing import Dict


def load_qid_to_wikidata(wikidata_json: str) -> Dict[str, Dict[str, str]]:
    """
    :param wikidata_json: path to Wikidata JSON
    :return: dict: QID -> Wikidata
    """

    with open(wikidata_json, 'r') as f:
        qid_to_wikidata = json.load(f)

    return qid_to_wikidata
