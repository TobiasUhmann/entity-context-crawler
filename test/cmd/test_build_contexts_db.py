from unittest import TestCase

import spacy
from spacy.lang.en import English

from cmd.build_contexts_db import crop_contexts


class Test(TestCase):
    def test_crop_contexts_1(self):
        page = 'This is a sentence. This is also a sentence. This is another one.'
        page_title = 'Foo Page'

        nlp: English = spacy.load('en_core_web_lg')
        ragged_context_rows = [(page[2:-2], page_title)]
        crop_sentences = False

        cropped_context_rows = crop_contexts(nlp, ragged_context_rows, crop_sentences)

        self.assertEqual(cropped_context_rows[0][0], 'is a sentence . This is also a sentence . This is another')
        self.assertEqual(cropped_context_rows[0][1], page_title)

    def test_crop_contexts_2(self):
        page = 'This is a sentence. This is also a sentence. This is another one.'
        page_title = 'Foo Page'

        nlp: English = spacy.load('en_core_web_lg')
        ragged_context_rows = [(page[2:-2], page_title)]
        crop_sentences = True

        cropped_context_rows = crop_contexts(nlp, ragged_context_rows, crop_sentences)

        self.assertEqual(cropped_context_rows, [])
