# This file is part of RinohType, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


import argparse
import os
import string

from xmlrpc.client import ServerProxy

import pip
import pkg_resources

from rinoh import paper

from rinoh.backend import pdf
from rinoh.font import TypefaceNotInstalled
from rinoh.frontend.rst import ReStructuredTextReader



def entry_point_name_to_identifier(entry_point_name):
    try:
        entry_point_name.encode('ascii')
        ascii_name = entry_point_name
    except UnicodeEncodeError:
        ascii_name = entry_point_name.encode('punycode').decode('ascii')
    return ''.join(char for char in ascii_name
                   if char in string.ascii_lowercase + string.digits)


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

    while True:
        try:
            from rinohlib.templates.article import Article, ArticleOptions
            break
        except TypefaceNotInstalled as err:
            print("Typeface '{}' not installed. Attempting to install it from "
                  "PyPI...".format(err.typeface_name))
            # answer = input()
            pypi = ServerProxy('https://pypi.python.org/pypi')
            typeface_id = entry_point_name_to_identifier(err.typeface_id)
            distribution_name_parts = ['rinoh', 'typeface', typeface_id]
            for pkg in pypi.search(dict(name=distribution_name_parts)):
                if pkg['name'] == '-'.join(distribution_name_parts):
                    typeface_pkg = pkg['name']
                    print("Installing typeface package '{}' using pip..."
                          .format(typeface_pkg))
                    pip.main(['install', typeface_pkg])
                    break
            else:
                raise SystemExit("No '{}' typeface found on PyPI. Aborting."
                                 .format(err.typeface_name))
            pkg_resources.working_set.__init__()      # rescan entry points

    parser = ReStructuredTextReader()
    with open(input_filename) as input_file:
        document_tree = parser.parse(input_file)
    options = ArticleOptions(page_size=page_size)
    document = Article(document_tree, options, backend=pdf)
    document.render(input_root)
