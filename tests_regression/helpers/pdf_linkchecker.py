# Adapted from a PDF test script by Tim Arnold
# http://reachtim.com/articles/PDF-Testing.html
# https://gist.github.com/tiarno/dea01f70a54cac52f6a6

import sys

from rinoh.backend.pdf import PDFReader



def check_pdf(pdf):
    links = list()
    urls = list()
    badurls = list()

    for page in pdf.catalog['Pages']['Kids']:
        obj = page.object
        for annot in [x.object for x in obj.get('Annots', [])]:
            if 'A' in annot and 'D' in annot['A']:
                links.append(str(annot['A']['D']))
            elif 'Dest' in annot:
                links.append(str(annot['Dest']))
                
    anchors = [str(key) for key in pdf.catalog['Names']['Dests']['Names'][::2]]
    superfluous_anchors = [x for x in anchors if x not in links]
    badlinks = [x for x in links if x not in anchors]
    return anchors, links, superfluous_anchors, badlinks, urls, badurls


def check_pdf_links(filename):
    pdf = PDFReader(filename)
    return check_pdf(pdf)


if __name__ == '__main__':
    fname = sys.argv[1]
    print('Checking %s' % fname)
    (anchors, links, superfluous_anchors,
     badlinks, urls, badurls) = check_pdf_links(fname)
    print('urls: ', ', '.join(urls))
    print
    print( 'anchors: ', ', '.join(anchors))
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
