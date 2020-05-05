from deepca.dumpr import dumpr

FULL_WIKIPEDIA_DOCS_XML = 'enwiki-latest-pages-articles.xml'


class LinkExtractor:
    full_wikipedia_docs_xml: str  # path/to/full_wikipedia_docs.xml

    def __init__(self, full_wikipedia_docs):
        self.full_wikipedia_docs_xml = full_wikipedia_docs

    def run(self):
        print('Link Extractor...')


if __name__ == '__main__':
    # TODO Pass file names on command line
    linkExtractor = LinkExtractor(FULL_WIKIPEDIA_DOCS_XML)
    linkExtractor.run()
