import lxml.etree as etree


def main():
    context = etree.iterparse('wikipedia.xml', events=['start', 'end'], encoding='utf-8')

    root = None
    page_count = 0

    for event, node in context:
        if event == 'start' and node.tag.endswith('mediawiki'):
            root = node
            for child in root:
                root.remove(child)

        elif event == 'end' and node.tag.endswith('siteinfo'):
            root.append(node)

        elif event == 'end' and node.tag.endswith('page'):
            root.append(node)
            page_count += 1
            if page_count == 1000:
                break

    with open('wikipedia-1000.xml', 'wb') as f:
        f.write(etree.tostring(root))


if __name__ == '__main__':
    main()
