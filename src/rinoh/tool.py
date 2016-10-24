# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


import argparse
import os

from rinoh import __version__, __release_date__

from rinoh.font import Typeface
from rinoh.frontend.rst import ReStructuredTextReader
from rinoh.paper import Paper, PAPER_BY_NAME
from rinoh.resource import ResourceNotInstalled
from rinoh.style import StyleSheet, StyleSheetFile
from rinoh.stylesheets import matcher
from rinoh.template import DocumentTemplate, TemplateConfigurationFile


DEFAULT = ' (default: %(default)s)'


parser = argparse.ArgumentParser(description='Render a reStructuredText '
                                             'document to PDF.')
parser.add_argument('input', type=str, nargs='?',
                    help='the reStructuredText document to render')
parser.add_argument('-t', '--template', type=str, default='article',
                    metavar='NAME OR FILENAME',
                    help='the document template or template configuration to '
                         'use' + DEFAULT)
parser.add_argument('-s', '--stylesheet', type=str, metavar='NAME OR FILENAME',
                    help='the style sheet used to style the document '
                         'elements '
                         + DEFAULT % dict(default="the template's default"))
parser.add_argument('-p', '--paper', type=str,
                    help='the paper size to render to '
                         + DEFAULT % dict(default="the template's default"))
parser.add_argument('--list-templates', action='store_true',
                    help='list the installed document templates and exit')
parser.add_argument('--list-stylesheets', action='store_true',
                    help='list the installed style sheets and exit')
parser.add_argument('--version', action='version',
                    version='%(prog)s {} ({})'.format(__version__,
                                                      __release_date__))


def main():
    global parser
    args = parser.parse_args()
    do_exit = False
    if args.list_templates:
        print('Installed document templates:')
        for name in sorted(DocumentTemplate.installed_resources):
            print('- {}'.format(name))
        do_exit = True
    if args.list_stylesheets:
        print('Installed style sheets:')
        for name in sorted(StyleSheet.installed_resources):
            print('- {}'.format(name))
        do_exit = True
    if do_exit:
        return

    try:
        input_dir, input_filename = os.path.split(args.input)
    except AttributeError:
        parser.print_help()
        return

    template_cfg = {}
    variables = {}
    if args.stylesheet:
        if os.path.exists(args.stylesheet):
            stylesheet = StyleSheetFile(args.stylesheet, matcher=matcher)
        else:
            try:
                stylesheet = StyleSheet.from_string(args.stylesheet)
            except ResourceNotInstalled as err:
                raise SystemExit("Could not find the Style sheet '{}'. "
                                 "Aborting.\n"
                                 "Run `{} --list-stylesheets` to find out "
                                 "which style sheets are available."
                                 .format(err.resource_name, parser.prog))
        template_cfg['stylesheet'] = stylesheet

    if args.paper:
        try:
            variables['paper_size'] = Paper.from_string(args.paper.lower())
        except ValueError:
            accepted = ', '.join(sorted(paper.name for paper
                                        in PAPER_BY_NAME.values()))
            raise SystemExit("Unknown paper size '{}'. Must be one of:\n"
                             "   {}".format(args.paper, accepted))

    input_root, input_ext = os.path.splitext(input_filename)
    parser = ReStructuredTextReader()
    with open(args.input) as input_file:
        document_tree = parser.parse(input_file)

    if os.path.isfile(args.template):
        template_cfg['base'] = TemplateConfigurationFile(args.template)
        template_cls = template_cfg['base'].document_template_class
    else:
        template_cls = DocumentTemplate.from_string(args.template)
    configuration = template_cls.Configuration('rinoh command line options',
                                               **template_cfg)
    configuration.variables.update(variables)
    document = template_cls(document_tree, configuration=configuration)
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
