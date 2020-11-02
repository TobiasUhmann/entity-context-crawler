from unittest import TestCase

import spacy
from spacy.lang.en import English

from cmd.build_contexts_db import crop_contexts


class Test(TestCase):
    def test_crop_contexts_1(self):
        page = 'This is a sentence. This is also a sentence. This is another one.'
        page_title = 'Foo Page'

        nlp: English = spacy.load('en_core_web_lg')
        ragged_contexts = [page[2:-2]]
        page_titles = [page_title]
        crop_sentences = False

        result_cropped_contexts, result_page_titles = \
            crop_contexts(nlp, ragged_contexts, page_titles, crop_sentences)

        self.assertEqual(result_cropped_contexts, ['is a sentence . This is also a sentence . This is another'])
        self.assertEqual(result_page_titles, [page_title])

    def test_crop_contexts_2(self):
        page = 'This is a sentence. This is also a sentence. This is another one.'
        page_title = 'Foo Page'

        nlp: English = spacy.load('en_core_web_lg')
        ragged_contexts = [page[2:-2]]
        page_titles = [page_title]
        crop_sentences = True

        result_cropped_contexts, result_page_titles = \
            crop_contexts(nlp, ragged_contexts, page_titles, crop_sentences)

        self.assertEqual(result_cropped_contexts, [])
        self.assertEqual(result_page_titles, [])
