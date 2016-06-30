# This file is part of RinohType, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


import argparse
import os

from rinoh import paper

from rinoh.backend import pdf
from rinoh.font import TypefaceNotInstalled, install_typeface
from rinoh.frontend.rst import ReStructuredTextReader
from rinoh.stylesheets import sphinx
from rinoh.template import DocumentOptions
from rinoh.templates import Article


def main():
    parser = argparse.ArgumentParser(description='Render a reStructuredText '
                                                 'document to PDF.')
    parser.add_argument('input', type=str, nargs='?',
                       help='the reStructuredText document to render')
    parser.add_argument('--paper', type=str, nargs='?', default='A4',
                       help='the paper size to render to (default: A4)')
    args = parser.parse_args()

    try:
        input_dir, input_filename = os.path.split(args.input)
    except AttributeError:
        parser.print_help()
        return

    try:
        page_size = getattr(paper, args.paper.upper())
    except AttributeError:
        print("Unknown paper size '{}'. Must be one of:".format(args.paper))
        print('   A0, A1, ..., A10, letter, legal, junior_legal, ledger, '
              'tabloid')
        return

    input_root, input_ext = os.path.splitext(input_filename)
    if input_dir:
        os.chdir(input_dir)

    parser = ReStructuredTextReader()
    with open(input_filename) as input_file:
        document_tree = parser.parse(input_file)
    options = DocumentOptions(stylesheet=sphinx)
    document = Article(document_tree, options=options, backend=pdf)

    while True:
        try:
            document.render(input_root)
            break
        except TypefaceNotInstalled as err:
            print("Typeface '{}' not installed. Attempting to install it from "
                  "PyPI...".format(err.typeface_name))
            # answer = input()
            success = install_typeface(err.entry_point_name)
            if not success:
                raise SystemExit("No '{}' typeface found on PyPI. Aborting."
                                 .format(err.typeface_name))
