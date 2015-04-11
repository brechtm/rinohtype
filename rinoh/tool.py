
import argparse
import os

from rinoh import paper

from rinoh.backend import pdf
from rinoh.frontend.rst import ReStructuredTextParser

from rinohlib.templates.article import Article, ArticleOptions


def main():
    parser = argparse.ArgumentParser(description='Render a reStructuredText '
                                                 'document to PDF.')
    parser.add_argument('input', type=str, nargs='?',
                       help='the reStructuredText document to render')
    parser.add_argument('--paper', type=str, nargs='?', default='A4',
                       help='the paper size to render to')
    args = parser.parse_args()

    try:
        input_dir, input_file = os.path.split(args.input)
    except AttributeError:
        parser.print_help()
        return

    input_base, input_ext = os.path.splitext(input_file)
    if input_dir:
        os.chdir(input_dir)
    parser = ReStructuredTextParser()
    document_tree = parser.parse(input_file)
    options = ArticleOptions(page_size=getattr(paper, args.paper.upper()))
    document = Article(document_tree, options, backend=pdf)
    document.render(input_base)
