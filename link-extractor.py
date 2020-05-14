import pickle
from collections import defaultdict

import wikitextparser as wtp

from wikipedia import Wikipedia

FULL_WIKIPEDIA_DOCS_XML = 'enwiki-latest-pages-articles.xml'


def dd():
    return defaultdict(set)


if __name__ == '__main__':
    with open(FULL_WIKIPEDIA_DOCS_XML, 'rb') as in_xml:

        #
        # Build graph
        #

        nodes = defaultdict(dd)

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
