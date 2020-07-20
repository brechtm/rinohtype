#! /usr/bin/env python

# usage: diffpdf.py file1.pdf file2.pdf

# requirements:
# - ImageMagick (convert)
# - MuPDF's mutool >= 1.13.0
#   or poppler's pdftoppm (known to work: 0.18.4, 0.41.0, 0.85.0, 0.89.0;
#                          known to fail: 0.42.0)

import argparse
import os
import shutil
import sys

from decimal import Decimal
from functools import partial
from multiprocessing import Pool, cpu_count
from shutil import which
from subprocess import Popen, PIPE, DEVNULL

from rinoh.backend.pdf import PDFReader


DIFF_DIR = 'pdfdiff'
SHELL = sys.platform == 'win32'


def diff_pdf(a_filename, b_filename, depth=None):
    a = PDFReader(a_filename)
    b = PDFReader(b_filename)
    a_numpages = int(a.catalog['Pages']['Count'])
    b_numpages = int(b.catalog['Pages']['Count'])

    success = True
    if a_numpages != b_numpages:
        print('PDF files have different lengths ({} and {})'
              .format(a_numpages, b_numpages))
        success = False

    sync_points = []
    if depth is not None:
        a_pages = list(a.catalog['Pages'].pages)
        b_pages = list(b.catalog['Pages'].pages)
        for (a_depth, a_title, a_dest), (b_depth, b_title, b_dest) \
                in zip(a.iter_outlines(depth), b.iter_outlines(depth)):
            a_page = a_pages.index(a_dest[0]) + 1
            b_page = b_pages.index(b_dest[0]) + 1
            if (a_depth, a_title) != (b_depth, b_title):
                print("PDF outlines diverge:\n"
                      "  '{a_title}' -> page {a_page} (depth {a_depth})\n"
                      "  '{b_title}' -> page {b_page} (depth {b_depth})"
                      .format(**locals()))
                success = False
                break
            if a_page != b_page:
                print("Matching PDF outline entries have different targets:\n"
                      "  '{a_title}' -> page {a_page} / {b_page}"
                      .format(**locals()))
                success = False
                sync_points.append((a_page, b_page))
    sync_points.append((a_numpages + 1, b_numpages + 1))

    if os.path.exists(DIFF_DIR):
        for item in os.listdir(DIFF_DIR):
            item_path = os.path.join(DIFF_DIR, item)
            if os.path.isfile(item_path):
                os.unlink(item_path)
            elif os.path.isdir(item_path):
                shutil.rmtree(item_path)
    else:
        os.mkdir(DIFF_DIR)

    a_start = b_start = 1
    for a_end, b_end in sync_points:
        print('Diffing pages {}..{} / {}..{}'.format(a_start, a_end - 1,
                                                     b_start, b_end - 1))
        if (a_end - a_start) != (b_end - b_start):
            print('Page ranges have a different length! Some pages will not '
                  'be compared.')
            success = False
        a_numbers = range(a_start, a_end)
        b_numbers = range(b_start, b_end)
        page_numbers = list(zip(a_numbers, b_numbers))

        # https://pymotw.com/2/multiprocessing/communication.html#process-pools
        pool_size = cpu_count()
        pool = Pool(processes=pool_size)
        print('Running {} processes in parallel'.format(pool_size))
        perform_diff = partial(diff_page, a_filename, b_filename)
        try:
            pool_outputs = pool.map(perform_diff, page_numbers)
        except CommandFailed as exc:
            raise SystemExit('Problem running mutool/pdftoppm'
                             ' or convert (page {})!'.format(exc.page_number))
        pool.close() # no more tasks
        pool.join()  # wrap up current tasks

        for (a_page, b_page), page_diff in zip(page_numbers, pool_outputs):
            if page_diff != 0:
                print('page {}/{} ({})'.format(a_page, b_page, page_diff))
                success = False

        a_start, b_start = a_end, b_end
    return success


class CommandFailed(Exception):
    def __init__(self, page_number):
        self.page_number = page_number


def diff_page(a_filename, b_filename, ab_page):
    a_page, b_page = ab_page
    if compare_page(a_filename, b_filename, a_page, b_page):
        return 0

    page_number = a_page
    diff_jpg_path = os.path.join(DIFF_DIR, '{}.jpg'.format(page_number))
    # http://stackoverflow.com/a/28779982/438249
    diff = Popen(['convert', '-', '(', '-clone', '0-1', '-compose', 'darken',
                                       '-composite', ')',
                  '-channel', 'RGB', '-combine', diff_jpg_path],
                 shell=SHELL, stdin=PIPE)
    a_page = pdf_page_to_ppm(a_filename, page_number, diff.stdin, gray=True)
    if a_page.wait() != 0:
        raise CommandFailed(page_number)
    b_page = pdf_page_to_ppm(b_filename, page_number, diff.stdin, gray=True)
    diff.stdin.close()
    if b_page.wait() != 0 or diff.wait() != 0:
        raise CommandFailed(page_number)
    grayscale = Popen(['convert', diff_jpg_path, '-colorspace', 'HSL',
                       '-channel', 'g', '-separate', '+channel', '-format',
                       '%[fx:mean]', 'info:'], shell=SHELL, stdout=PIPE)
    return Decimal(grayscale.stdout.read().decode('ascii'))


def compare_page(a_filename, b_filename, a_page, b_page):
    """Returns ``True`` if the pages at ``page_number`` are identical"""
    compare = Popen(['compare', '-', '-metric', 'AE', 'null:'],
                    shell=SHELL, stdin=PIPE, stdout=DEVNULL, stderr=DEVNULL)
    a_page = pdf_page_to_ppm(a_filename, a_page, compare.stdin)
    if a_page.wait() != 0:
        raise CommandFailed(a_page)
    b_page = pdf_page_to_ppm(b_filename, b_page, compare.stdin)
    compare.stdin.close()
    if b_page.wait() != 0:
        raise CommandFailed(b_page)
    return compare.wait() == 0


def pdftoppm(pdf_path, page_number, stdout, gray=False):
    command = ['pdftoppm', '-f', str(page_number),
               '-singlefile', str(pdf_path)]
    if gray:
        command.insert(-1, '-gray')
    return Popen(command, shell=SHELL, stdout=stdout)


def mutool(pdf_path, page_number, stdout, gray=False):
    command = ['mutool', 'draw', '-r', '150', '-F', 'ppm', '-o', '-',
               str(pdf_path), str(page_number)]
    if gray:
        command.insert(-2, '-c')
        command.insert(-2, 'gray')
    return Popen(command, shell=SHELL, stdout=stdout, stderr=DEVNULL)


if which('mutool'):
    pdf_page_to_ppm = mutool
elif which('pdftoppm'):
    pdf_page_to_ppm = pdftoppm
else:
    print("mutool or poppler's pdftoppm is required", file=sys.stderr)
    raise SystemExit(2)


parser = argparse.ArgumentParser(description='Visual PDF diff.')
parser.add_argument('file1', metavar='FILE1', type=str,
                    help='Path to the reference PDF')
parser.add_argument('file2', metavar='FILE2', type=str,
                    help='Path of the PDF to diff against the reference PDF')
parser.add_argument('-s', '--split', metavar='DEPTH', type=int,
                    help='Reset the diff at the page numbers corresponding '
                         'to every outline entry up to DEPTH. For example, a '
                         'DEPTH of 0 limits this to the top-level outlines '
                         'entries (e.g. chapters).')


if __name__ == '__main__':
    args = parser.parse_args()
    rc = 0 if diff_pdf(args.file1, args.file2, depth=args.split) else 1
    raise SystemExit(rc)
