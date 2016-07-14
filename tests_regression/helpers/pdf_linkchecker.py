# Adapted from a PDF test script by Tim Arnold
# http://reachtim.com/articles/PDF-Testing.html
# https://gist.github.com/tiarno/dea01f70a54cac52f6a6

import sys
import urllib

from PyPDF2 import PdfFileReader

import requests


def check_ftp(url):
    try:
        response = urllib.urlopen(url)
    except IOError as e:
        result, reason = False, e
    else:
        if response.read():
            result, reason = True, 'okay'
        else:
            result, reason = False, 'Empty Page'
    return result, reason


def check_url(url, auth=None):
    headers = {'User-Agent': 'Mozilla/5.0', 'Accept': '*/*'}
    if url.startswith('ftp://'):
        result, reason = check_ftp(url)
    else:
        try:
            response = requests.get(url, timeout=6, auth=auth, headers=headers)
        except (requests.ConnectionError,
                requests.HTTPError,
                requests.Timeout,
                requests.exceptions.MissingSchema,
                requests.exceptions.InvalidSchema) as e:
            result, reason = False, e
        else:
            if response.text:
                result, reason = response.status_code, response.reason
            else:
                result, reason = False, 'Empty Page'

    return result, reason


def check_pdf(pdf):
    links = list()
    urls = list()
    badurls = list()

    for page in pdf.pages:
        obj = page.getObject()
        for annot in [x.getObject() for x in obj.get('/Annots', [])]:
            if '/A' in annot:
                dst = annot['/A'].get('/D')
                url = annot['/A'].get('/URI')
                if dst:
                    links.append(dst)
                elif url:
                    continue
                    urls.append(url)
                    result, reason = check_url(url)
                    if not result:
                        badurls.append({'url':url, 'reason': '%r' % reason})
            elif '/Dest' in annot:
                links.append(annot['/Dest'])
                

    anchors = pdf.namedDestinations.keys()
    superfluous_anchors = [x for x in anchors if x not in links]
    badlinks = [x for x in links if x not in anchors]
    return anchors, links, superfluous_anchors, badlinks, urls, badurls


def check_pdf_links(filename):
    pdf = PdfFileReader(filename)
    return check_pdf(pdf)


if __name__ == '__main__':
    fname = sys.argv[1]
    print('Checking %s' % fname)
    pdf = PdfFileReader(fname)
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
