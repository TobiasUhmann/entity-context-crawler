from typing import List

from spacy.language import Language
from spacy.matcher import PhraseMatcher


def mask_contexts(nlp: Language, unmasked_contexts: List[str], masks: List[str]) -> List[str]:
    """ Replace all occurrences of all masks with hashes """

    matcher = PhraseMatcher(nlp.vocab)
    patterns = list(nlp.pipe(masks))
    matcher.add('Entities', None, *patterns)

    masked_contexts = []
    for unmasked_context in unmasked_contexts:
        spacy_doc = nlp.make_doc(unmasked_context)
        matches = matcher(spacy_doc)

        def contains(x, y):
            return x[0] <= y[0] and x[1] >= y[1] and (x[0] != y[0] or x[1] != y[1])

        spans = {(start, end) for match_id, start, end in matches}
        kept_spans = []
        for span in spans:
            keep_span = True
            for other_span in spans.difference({span}):
                if contains(other_span, span):
                    keep_span = False
                    break

            if keep_span:
                kept_spans.append(span)

        mutable_context = list(unmasked_context)
        for start, end in kept_spans:
            match_span = spacy_doc[start:end]

            start_char = match_span.start_char
            end_char = match_span.end_char

            for i in range(start_char, end_char):
                mutable_context[i] = '#'

        masked_context = ''.join(mutable_context)
        masked_contexts.append(masked_context)

    return masked_contexts
