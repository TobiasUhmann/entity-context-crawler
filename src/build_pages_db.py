import wikitextparser as wtp

from util.util import log
from util.wikipedia import Wikipedia


def _process_raw_wiki_xml(raw_wiki_xml):
    """ Iterate through all raw Wiki pages and store them in the pages DB """

    with open(raw_wiki_xml, 'rb') as raw_wiki_xml_fh:
        wikipedia = Wikipedia(raw_wiki_xml_fh, tag='page')
        for page_count, page in enumerate(wikipedia):

            page_markup = page['text']
            core_markup = _get_core_markup(page_markup)

            try:
                wtp.parse(page_markup).plain_text()
            except:
                print(page_count)

            if page_count % 100 == 0:
                log(str(page_count))


def _get_core_markup(markup: str) -> str:
    parsed = wtp.parse(markup)

    intro = parsed.get_sections(include_subsections=False, level=0)[0]
    sections = parsed.get_sections(include_subsections=True, level=2)

    section_blacklist = {'see also', 'references', 'further reading', 'external links'}
    filtered_sections = [section for section in sections
                         if section.title.strip().lower() not in section_blacklist]

    intro_markup = intro.contents
    section_markups = [section.contents for section in filtered_sections]

    markups = [intro_markup]
    markups.extend(section_markups)

    return '\n'.join(markups)


if __name__ == '__main__':
    _process_raw_wiki_xml('data/enwiki-20200920.xml')
