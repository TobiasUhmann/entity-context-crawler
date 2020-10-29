from unittest import TestCase

import spacy
from spacy.lang.en import English

from cmd.build_contexts_db import crop_contexts


class Test(TestCase):
    def test_crop_contexts_1(self):
        page = 'This is a sentence. This is also a sentence. This is another one.'

        nlp: English = spacy.load('en_core_web_lg')
        ragged_contexts = [page[2:-2]]
        crop_sentences = False

        cropped_contexts = crop_contexts(nlp, ragged_contexts, crop_sentences)

        expected_cropped_contexts = ['is a sentence . This is also a sentence . This is another']
        self.assertEqual(cropped_contexts, expected_cropped_contexts)

    def test_crop_contexts_2(self):
        page = 'This is a sentence. This is also a sentence. This is another one.'

        nlp: English = spacy.load('en_core_web_lg')
        ragged_contexts = [page[2:-2]]
        crop_sentences = True

        cropped_contexts = crop_contexts(nlp, ragged_contexts, crop_sentences)

        expected_cropped_contexts = []
        self.assertEqual(cropped_contexts, expected_cropped_contexts)
