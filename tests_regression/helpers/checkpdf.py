#! /usr/bin/env python

# Adapted from a PDF test script by Tim Arnold
# http://reachtim.com/articles/PDF-Testing.html
# https://gist.github.com/tiarno/dea01f70a54cac52f6a6

import sys

from collections import namedtuple

from rinoh.backend.pdf import PDFReader


# a link resolved to the page it points to and the position on that page
LinkTarget = namedtuple('LinkTarget', ['source_page', 'target_page', 'left',
                                       'top'])

# a link as it appears in the document: the page it is on and its raw
# destination (explicit array or named destination)
Link = namedtuple('Link', ['source_page', 'destination'])


def page_index_map(pdf):
    """Map every page object of `pdf` to its page number (one-based)"""
    return {id(page): number
            for number, page in enumerate(pdf.catalog['Pages'].pages, 1)}


def resolve_destination(pdf, page_numbers, destination):
    """Resolve a link `destination` to ``(page number, left, top)``

    The destination is either an explicit array (``[page /XYZ left top zoom]``)
    or the name of an entry in the document's named destination dictionary. The
    name itself is meaningless for regression testing (its object IDs depend on
    the tool that generated the document), so the destination is resolved to
    the target page number and the position on that page instead.
    """
    try:
        dest = pdf.dests[destination]
    except (KeyError, TypeError):
        dest = destination
    try:
        page_object, _, left, top = dest[:4]
    except (TypeError, ValueError):
        return None
    page_number = page_numbers.get(id(page_object))
    if page_number is None:
        return None
    return page_number, float(left), float(top)


def iter_links(pdf):
    """Yield a :class:`Link` for every link annotation in `pdf`"""
    for source_page, page in enumerate(pdf.catalog['Pages']['Kids'], 1):
        obj = page.object
        for annot in [x.object for x in obj.get('Annots', [])]:
            if 'A' in annot and 'D' in annot['A']:
                yield Link(source_page, annot['A']['D'])
            elif 'Dest' in annot:
                yield Link(source_page, annot['Dest'])


def link_target(link, pdf, page_numbers):
    """Resolve a :class:`Link` to a :class:`LinkTarget`

    Returns `None` if the link's destination cannot be resolved to a page.
    """
    target = resolve_destination(pdf, page_numbers, link.destination)
    if target is None:
        return None
    target_page, left, top = target
    return LinkTarget(link.source_page, target_page, left, top)


def link_targets(pdf):
    """List the resolved target of every link in `pdf`"""
    page_numbers = page_index_map(pdf)
    targets = (link_target(link, pdf, page_numbers)
               for link in iter_links(pdf))
    return [target for target in targets if target is not None]


def check_pdf(pdf):
    urls = list()
    badurls = list()
    anchors = [str(name) for name in pdf.dests]
    outlines = list(iter_outlines(pdf.catalog['Outlines']))

    page_numbers = page_index_map(pdf)
    links = list()
    targets = list()
    for link in iter_links(pdf):
        links.append(str(link.destination))
        target = link_target(link, pdf, page_numbers)
        if target is not None:
            targets.append(target)

    superfluous_anchors = [x for x in anchors if x not in links]
    badlinks = [x for x in links if x not in anchors]
    badoutlinelinks = [str(target) for _, _, target in outlines
                       if str(target) not in anchors]
    return (anchors, links, targets, superfluous_anchors,
            badlinks, badoutlinelinks, urls, badurls, outlines)


def iter_outlines(outlines, level=0):
    if 'Title' in outlines:
        yield level, outlines['Title'], outlines['Dest']
    if 'First' in outlines:
        yield from iter_outlines(outlines['First'], level + 1)
    if 'Next' in outlines:
        yield from iter_outlines(outlines['Next'], level)


def check_pdf_links(filename):
    pdf = PDFReader(filename)
    return check_pdf(pdf)


if __name__ == '__main__':
    fname = sys.argv[1]
    print('Checking %s' % fname)
    pdf = PDFReader(fname)
    (anchors, links, targets, superfluous_anchors, badlinks,
     badoutlinelinks, urls, badurls, outlines) = check_pdf(pdf)
    print('urls: ', ', '.join(urls))
    print()
    print('anchors: ', ', '.join(anchors))
    print()
    print('superfluous_anchors: ', ', '.join(superfluous_anchors))
    print()
    print('links: ', ', '.join(links))
    print()
    print('link targets:')
    for target in targets:
        print('  {}'.format(target))
    print()
    print('bad links: ', ', '.join(badlinks))
    print()
    print('bad outline links: ', ', '.join(badoutlinelinks))
    print()
    print('bad urls:')
    for item in badurls:
        for key, value in item.items():
            print('  {}: {}'.format(key, value))
    print()
    print('outlines:')
    page_numbers = page_index_map(pdf)
    for level, title, dest in outlines:
        target = resolve_destination(pdf, page_numbers, dest)
        page = target[0] if target is not None else None
        print('{:4} {!s:20} {}{}  (page {})'.format(
            level, dest, '  ' * (level - 1), title, page))
