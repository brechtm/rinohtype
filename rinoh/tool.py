
import argparse
import os

from rinoh import paper

from rinoh.backend import pdf
from rinoh.frontend.rst import ReStructuredTextReader

from rinohlib.templates.article import Article, ArticleOptions


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
    options = ArticleOptions(page_size=page_size)
    document = Article(document_tree, options, backend=pdf)
    document.render(input_root)
