# https://stackoverflow.com/a/55147982/4540114

from lxml import etree


class Wikipedia:
    def __init__(self, fh, tag):
        """
        Initialize 'iterparse' to only generate 'end' events on tag '<entity>'

        :param fh: File Handle from the XML File to parse
        :param tag: The tag to process
        """
        # Prepend the default Namespace {*} to get anything.
        self.context = etree.iterparse(fh, events=("end",), tag=['{*}' + tag])

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

        :return: Dict var 'entity' {tag1, value, tag2, value, ... ,tagn, value}}
        """

        for event, elem in self._parse():
            namespaces = {'xmlns': etree.QName(elem).namespace}

            titles = elem.xpath('./xmlns:title/text()', namespaces=namespaces)
            if titles:
                title = titles[0]
            else:
                continue

            redirects = elem.xpath('./xmlns:redirect/@title', namespaces=namespaces)
            redirect = redirects[0] if redirects else None

            texts = elem.xpath('./xmlns:revision/xmlns:text/text()', namespaces=namespaces)
            if texts:
                text = texts[0]
            else:
                continue

            if not title.startswith('Template:'):
                yield {'title': title, 'redirect': redirect, 'text': text}


if __name__ == "__main__":
    with open('../data/enwiki-latest-pages-articles.xml', 'rb') as in_xml:
        for record in Wikipedia(in_xml, tag='page'):
            print("record:{}".format(record))
