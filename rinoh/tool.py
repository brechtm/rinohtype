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
from rinoh.font import Typeface
from rinoh.frontend.rst import ReStructuredTextReader
from rinoh.resource import ResourceNotInstalled
from rinoh.style import StyleSheet
from rinoh.templates import Article


DEFAULT = ' (default: %(default)s)'


def main():
    parser = argparse.ArgumentParser(description='Render a reStructuredText '
                                                 'document to PDF.')
    parser.add_argument('input', type=str, nargs='?',
                       help='the reStructuredText document to render')
    parser.add_argument('-s', '--stylesheet', type=str, nargs='?',
                        default='sphinx_article',
                        help='the style sheet used to style the document '
                             'elements' + DEFAULT)
    parser.add_argument('-p', '--paper', type=str, nargs='?', default='A4',
                       help='the paper size to render to ' + DEFAULT)
    args = parser.parse_args()

    try:
        input_dir, input_filename = os.path.split(args.input)
    except AttributeError:
        parser.print_help()
        return

    kwargs = {}
    try:
        kwargs['stylesheet'] = StyleSheet.from_string(args.stylesheet)
    except ResourceNotInstalled as err:
        raise SystemExit("Could not find the Style sheet '{}'. Aborting."
                         .format(err.resource_name))

    try:
        page_size = getattr(paper, args.paper.upper()) # TODO: use variable
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

    configuration = Article.Configuration(**kwargs)
    document = Article(document_tree, configuration=configuration, backend=pdf)

    while True:
        try:
            document.render(input_root)
            break
        except ResourceNotInstalled as err:
            print("Typeface '{}' not installed. Attempting to install it from "
                  "PyPI...".format(err.resource_name))
            # answer = input()
            success = Typeface.install_from_pypi(err.entry_point_name)
            if not success:
                raise SystemExit("No '{}' typeface found on PyPI. Aborting."
                                 .format(err.resource_name))
