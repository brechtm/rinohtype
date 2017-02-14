#! /usr/bin/env python

# usage: diffpdf.py file1.pdf file2.pdf

# requirements:
# - ImageMagick (convert)
# - Poppler's pdftoppm and pdfinfo tools (works with 0.18.4 and 0.41.0,
#                                         fails with 0.42.0)
#   (could be replaced with Ghostscript if speed is
#    not important - see commented commands below)

import os
import shutil
import sys

from decimal import Decimal
from functools import partial
from multiprocessing import Pool, cpu_count
from subprocess import Popen, PIPE

from rinoh.backend.pdf import PDFReader


DIFF_DIR = 'pdfdiff'
SHELL = sys.platform == 'win32'


def diff_pdf(a_filename, b_filename):
    a_pages = PDFReader(a_filename).catalog['Pages']['Count']
    b_pages = PDFReader(b_filename).catalog['Pages']['Count']

    success = True
    if a_pages != b_pages:
        print('PDF files have different lengths ({} and {})'
              .format(a_pages, b_pages))
        success = False

    if os.path.exists(DIFF_DIR):
        for item in os.listdir(DIFF_DIR):
            item_path = os.path.join(DIFF_DIR, item)
            if os.path.isfile(item_path):
                os.unlink(item_path)
            elif os.path.isdir(item_path):
                shutil.rmtree(item_path)
    else:
        os.mkdir(DIFF_DIR)

    min_pages = min(a_pages, b_pages)
    page_numbers = list(range(1, min_pages + 1))
    # https://pymotw.com/2/multiprocessing/communication.html#process-pools
    pool_size = cpu_count()
    pool = Pool(processes=pool_size)
    print('Running {} processes in parallel'.format(pool_size))
    perform_diff = partial(diff_page, a_filename, b_filename)
    try:
        pool_outputs = pool.map(perform_diff, page_numbers)
    except CommandFailed as exc:
        raise SystemExit('Problem running pdftoppm or convert (page {})!'
                         .format(exc.page_number))
    pool.close() # no more tasks
    pool.join()  # wrap up current tasks

    for page_number, page_diff in zip(page_numbers, pool_outputs):
        if page_diff != 0:
            print('page {} ({})'.format(page_number, page_diff))
            success = False
    return success


class CommandFailed(Exception):
    def __init__(self, page_number):
        self.page_number = page_number


def diff_page(a_filename, b_filename, page_number):
    diff_jpg_path = os.path.join(DIFF_DIR, '{}.jpg'.format(page_number))
    # http://stackoverflow.com/a/28779982/438249
    diff = Popen(['convert', '-', '(', '-clone', '0-1', '-compose', 'darken',
                                       '-composite', ')',
                  '-channel', 'RGB', '-combine', diff_jpg_path],
                 shell=SHELL, stdin=PIPE)
    a_page = pdf_page_to_grayscale_miff(a_filename, page_number, diff.stdin)
    if a_page.wait() != 0:
        raise CommandFailed(page_number)
    b_page = pdf_page_to_grayscale_miff(b_filename, page_number, diff.stdin)
    diff.stdin.close()
    if b_page.wait() != 0 or diff.wait() != 0:
        raise CommandFailed(page_number)
    grayscale = Popen(['convert', diff_jpg_path, '-colorspace', 'HSL',
                       '-channel', 'g', '-separate', '+channel', '-format',
                       '%[fx:mean]', 'info:'], shell=SHELL, stdout=PIPE)
    return Decimal(grayscale.stdout.read().decode('ascii'))


def pdf_page_to_grayscale_miff(pdf_path, page_number, stdout):
    pdftoppm = Popen(['pdftoppm', '-f', str(page_number), '-singlefile',
                      '-gray', pdf_path], shell=SHELL, stdout=PIPE)
    convert = Popen(['convert', '-', 'miff:-'],
                    shell=SHELL, stdin=pdftoppm.stdout, stdout=stdout)
    return convert


if __name__ == '__main__':
    _, a_filename, b_filename = sys.argv
    rc = 0 if diff_pdf(a_filename, b_filename) else 1
    raise SystemExit(rc)
