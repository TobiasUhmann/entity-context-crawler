from lxml import etree


class Wikipedia:
    missing_titles = 0
    missing_texts = 0
    skipped_special_pages = 0

    def __init__(self, fh, limit_pages = None):
        """
        Initialize 'iterparse' to only generate 'end' events on tag '<page>'

        :param fh: File Handle from the XML File to parse
        """

        # Prepend the default Namespace {*} to get anything.
        self.context = etree.iterparse(fh, events=("end",), tag=['{*}page'])
        self.limit_pages = limit_pages

    def _parse(self):
        """
        Parse the XML File for all '<tag>...</tag>' Elements
        Clear/Delete the Element Tree after processing

        :return: Yield the current 'Event, Element Tree'
        """
        for event, elem in self.context:
            yield event, elem

            elem.clear()
            while elem.getprevious() is not None:
                del elem.getparent()[0]

    def __iter__(self):
        """
        Iterate all '<tag>...</tag>' Element Trees yielded from self._parse()

        :return: Dict var 'entity' {tag_1, value, tag_2, value, ... ,tag_n, value}}
        """

        for count, parsed in enumerate(self._parse()):
            if self.limit_pages and count == self.limit_pages:
                break

            event, elem = parsed

            namespaces = {'xmlns': etree.QName(elem).namespace}

            titles = elem.xpath('./xmlns:title/text()', namespaces=namespaces)
            if titles:
                title = titles[0]
            else:
                self.missing_titles += 1
                continue

            redirects = elem.xpath('./xmlns:redirect/@title', namespaces=namespaces)
            redirect = redirects[0] if redirects else None

            texts = elem.xpath('./xmlns:revision/xmlns:text/text()', namespaces=namespaces)
            if texts:
                text = texts[0]
            else:
                self.missing_texts += 1
                continue

            namespaces = ('Talk:', 'User:', 'User talk:', 'Wikipedia:', 'Wikipedia talk:', 'File:', 'File talk:',
                          'MediaWiki:', 'MediaWiki talk:', 'Template:', 'Template talk:', 'Help:', 'Help talk:',
                          'Category:', 'Category talk:', 'Portal:', 'Portal talk:', 'Book:', 'Book talk:', 'Draft:',
                          'Draft talk:', 'Education Program:', 'Education Program talk:', 'TimedText:',
                          'TimedText talk:', 'Module:', 'Module talk:', 'Gadget:', 'Gadget talk:',
                          'Gadget definition:', 'Gadget definition talk:')

            if title.startswith(namespaces):
                self.skipped_special_pages += 1
                continue

            yield {'title': title, 'redirect': redirect, 'text': text}


if __name__ == "__main__":
    with open('../data/enwiki-latest-pages-articles.xml', 'rb') as in_xml:
        for record in Wikipedia(in_xml):
            print("record:{}".format(record))
