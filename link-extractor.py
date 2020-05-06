from deepca.dumpr import dumpr
import wikitextparser as wtp

from wikipedia import Wikipedia

FULL_WIKIPEDIA_DOCS_XML = 'enwiki-latest-pages-articles.xml'


class LinkExtractor:
    full_wikipedia_docs_xml: str  # path/to/full_wikipedia_docs.xml

    def __init__(self, full_wikipedia_docs):
        self.full_wikipedia_docs_xml = full_wikipedia_docs

    def run(self):
        print('Link Extractor...')

        with dumpr.BatchReader(self.full_wikipedia_docs_xml) as reader:
            for counter, dumpr_doc in enumerate(reader.docs):

                print('test')
                print(counter)
                print(dumpr_doc)
                print()


if __name__ == '__main__':
    with open('enwiki-latest-pages-articles.xml', 'rb') as in_xml:
        for page in Wikipedia(in_xml, tag='page'):
            print(page['title'][0])
            redirect = page['redirect']
            if redirect:
                print(page['redirect'][0])
            parsed = wtp.parse(page['text'][0])
            print(parsed.wikilinks)

    # TODO Pass file names on command line
    # linkExtractor = LinkExtractor(FULL_WIKIPEDIA_DOCS_XML)
    # linkExtractor.run()
