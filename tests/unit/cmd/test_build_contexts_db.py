from unittest import TestCase

import spacy
from spacy.lang.en import English
from spacy.matcher import PhraseMatcher

from cmd.build_contexts_db import crop_contexts


class Test(TestCase):
    def test_crop_contexts_1(self):
        page_text = 'Germany is a country in Europe. About 80 million people live in Germany.' \
                    ' Its capital is Berlin. In the west Germany borders on France.'
        page_title = 'Germany'

        raw_context = page_text[2:-2]

        nlp: English = spacy.load('en_core_web_lg')
        ragged_context_rows = [(raw_context, page_title)]
        crop_sentences = True

        entity_matcher = PhraseMatcher(nlp.vocab)
        entity_matcher.add('', None, *list(nlp.pipe(['Germany'])))

        cropped_context_rows = crop_contexts(nlp, ragged_context_rows, crop_sentences, entity_matcher)

        expected_cropped_context = 'About 80 million people live in Germany.'
        self.assertEqual(cropped_context_rows[0][0], expected_cropped_context)
        self.assertEqual(cropped_context_rows[0][1], page_title)
