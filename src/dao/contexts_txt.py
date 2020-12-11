from collections import defaultdict
from typing import Dict, Set


def load_contexts(contexts_txt: str) -> Dict[int, Set[str]]:

    ent_to_contexts: Dict[int, Set[str]] = defaultdict(set)

    with open(contexts_txt, encoding='utf-8') as fh:
        lines = fh.readlines()

    for line in lines[1:]:
        ent, _, context = line.split(' | ')
        ent_to_contexts[int(ent)].add(context)

    return ent_to_contexts
