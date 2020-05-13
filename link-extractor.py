import pickle
from collections import defaultdict

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


def dd():
    return defaultdict(set)


nodes = defaultdict(dd)

if __name__ == '__main__':
    with open('enwiki-latest-pages-articles.xml', 'rb') as in_xml:

        #
        # Build graph
        #

        for counter, page in enumerate(Wikipedia(in_xml, tag='page')):
            print(counter)
            if counter == 1000:
                break

            title = page['title'][0].lower()
            if page['redirect']:
                redirect = page['redirect'][0].lower()
                nodes[title]['redirect'].add(redirect)

            wikilinks = wtp.parse(page['text'][0]).wikilinks
            for wikilink in wikilinks:
                link_title = wikilink.title.lower()
                nodes[title]['links_to'].add(link_title)
                nodes[link_title]['linked_by'].add(title)

        #
        # Remove redirects from graph
        #



        #
        # Persist graph
        #

        pickle.dump(nodes, open('links.p', 'wb'))

    # TODO Pass file names on command line
    # linkExtractor = LinkExtractor(FULL_WIKIPEDIA_DOCS_XML)
    # linkExtractor.run()
