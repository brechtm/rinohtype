
import argparse
import os

from rinoh.backend import pdf
from rinoh.frontend.rst import ReStructuredTextParser

from rinohlib.templates.article import Article


def main():
    parser = argparse.ArgumentParser(description='Render a reStructuredText '
                                                 'document.')
    parser.add_argument('input', type=str, nargs='?',
                       help='the reStructuredText document to render')
    args = parser.parse_args()

    input_dir, input_file = os.path.split(args.input)
    input_base, input_ext = os.path.splitext(input_file)

    os.chdir(input_dir)
    parser = ReStructuredTextParser()
    document_tree = parser.parse(input_file)
    document = Article(document_tree, backend=pdf)
    document.render(input_base)
