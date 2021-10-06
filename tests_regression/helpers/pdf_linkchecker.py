# Adapted from a PDF test script by Tim Arnold
# http://reachtim.com/articles/PDF-Testing.html
# https://gist.github.com/tiarno/dea01f70a54cac52f6a6

import sys

from itertools import zip_longest

from rinoh.backend.pdf import PDFReader



def check_pdf(pdf):
    urls = list()
    badurls = list()
    anchors = [str(key) for key in pdf.catalog['Names']['Dests']['Names'][::2]]
    outlines = list(iter_outlines(pdf.catalog['Outlines']))

    links = list()
    for page in pdf.catalog['Pages']['Kids']:
        obj = page.object
        for annot in [x.object for x in obj.get('Annots', [])]:
            if 'A' in annot and 'D' in annot['A']:
                links.append(str(annot['A']['D']))
            elif 'Dest' in annot:
                links.append(str(annot['Dest']))

    superfluous_anchors = [x for x in anchors if x not in links]
    badlinks = [x for x in links if x not in anchors]
    badoutlinelinks = [str(target) for _, _, target in outlines
                       if str(target) not in anchors]
    return (anchors, links, superfluous_anchors,
            badlinks, badoutlinelinks, urls, badurls, outlines)


def iter_outlines(outlines, level=0):
    if 'Title' in outlines:
        yield level, outlines['Title'], outlines['Dest']
    if 'First' in outlines:
        yield from iter_outlines(outlines['First'], level + 1)
    if 'Next' in outlines:
        yield from iter_outlines(outlines['Next'], level)


def diff_outlines(reference, outlines):
    for ref, out in zip_longest(reference, outlines,
                                fillvalue=(None, None, None)):
        (l1, title1, id1), (l2, title2, id2) = ref, out
        if l1 != l2 or title1 != title2:
            return False
    return True


def check_pdf_links(filename):
    pdf = PDFReader(filename)
    return check_pdf(pdf)


if __name__ == '__main__':
    fname = sys.argv[1]
    print('Checking %s' % fname)
    (anchors, links, superfluous_anchors,
     badlinks, urls, badurls, outlines) = check_pdf_links(fname)
    print('urls: ', ', '.join(urls))
    print
    print('anchors: ', ', '.join(anchors))
    print
    print('superfluous_anchors: ', ', '.join(superfluous_anchors))
    print
    print('links: ', ', '.join(links))
    print
    print('bad links: ', ', '.join(badlinks))
    print
    print('bad urls:')
    for item in badurls:
        for key, value in item.items():
            print('  {}: {}'.format(key, value))
    print()
    print('outlines:')
    for level, title, dest in iter_outlines(outlines):
        print('{:4} {!s:20} {}'.format(level, dest, title))
