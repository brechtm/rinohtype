# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


import argparse
import os
import sys
import webbrowser

from collections import OrderedDict
from contextlib import suppress
from pathlib import Path
from platform import platform

from rinoh import __version__, __release_date__

from rinoh.attribute import Source
from rinoh.color import BLACK
from rinoh.dimension import PT, PERCENT
from rinoh.document import DocumentTree
from rinoh.draw import Stroke
from rinoh.flowable import StaticGroupedFlowables, GroupedFlowablesStyle
from rinoh.font import Typeface, FontSlant, FontWeight, FontWidth
from rinoh.font.google import installed_google_fonts_typefaces
from rinoh.paper import Paper, PAPER_BY_NAME
from rinoh.paragraph import ParagraphStyle, Paragraph, TabStop
from rinoh.resource import find_entry_points, ResourceNotFound
from rinoh.style import StyleSheet, StyleSheetFile
from rinoh.template import DocumentTemplate, TemplateConfigurationFile
from rinoh.templates import Article


DESCRIPTION = 'Render a structured document to PDF.'

DOCS_URL = 'http://www.mos6581.org/rinohtype/'

DEFAULT = ' (default: %(default)s)'


parser = argparse.ArgumentParser('rinoh', description=DESCRIPTION)
parser.add_argument('input', type=str, nargs='?',
                    help='the document to render')
parser.add_argument('-f', '--format', type=str,
                    help='the format of the input file'
                         + DEFAULT % dict(default='autodetect'))
parser.add_argument('-o', '--option', type=str, action='append', nargs=1,
                    default=[], metavar='OPTION=VALUE',
                    help='options to be passed to the input file reader')
parser.add_argument('-t', '--template', type=str, default='article',
                    metavar='NAME or FILENAME',
                    help='the document template or template configuration '
                         'file to use' + DEFAULT)
parser.add_argument('-s', '--stylesheet', type=str, metavar='NAME or FILENAME',
                    help='the style sheet used to style the document '
                         'elements '
                         + DEFAULT % dict(default="the template's default"))
parser.add_argument('-O', '--output', type=str,
                    metavar='FILENAME or DIRECTORY',
                    help='write the PDF output to FILENAME or to an existing '
                         'DIRECTORY with a filename derived from the input '
                         'filename (default: the current working directory)')
parser.add_argument('-p', '--paper', type=str,
                    help='the paper size to render to '
                         + DEFAULT % dict(default="the template's default"))
parser.add_argument('-i', '--install-resources', action='store_true',
                    help='automatically install missing resources (fonts, '
                         'templates, style sheets) from PyPI')
parser.add_argument('--list-templates', action='store_true',
                    help='list the installed document templates and exit')
parser.add_argument('--list-stylesheets', action='store_true',
                    help='list the installed style sheets and exit')
parser.add_argument('--list-fonts', metavar='FILENAME', type=str, nargs='?',
                    const=object,
                    help='list the installed fonts or, if FILENAME is given, '
                         'write a PDF file displaying all the fonts')
parser.add_argument('--list-formats', action='store_true',
                    help='list the supported input formats and exit')
parser.add_argument('--list-options', metavar='FRONTEND', type=str,
                    help='list the options supported by the given frontend '
                         'and exit')
parser.add_argument('--version', action='version',
                    version='%(prog)s {} ({})'.format(__version__,
                                                      __release_date__))
parser.add_argument('--versions', action='store_true',
                    help='list versions of rinohtype and related software (for '
                         'inclusion in bug reports)')
parser.add_argument('--docs', action='store_true',
                    help='open the online documentation in the default '
                         'browser')


def get_distribution_name(dist):
    return ('built-in' if dist.metadata['Name'] == 'rinohtype'
            else '{0[Name]} {0[Version]}'.format(dist.metadata))


def get_reader_by_name(format_name):
    for entry_point, _ in find_entry_points('rinoh.frontends', format_name):
        return entry_point.name, entry_point.load()
    raise SystemExit("Unknown format '{}'. Run `{} --list-formats` to "
                     "find out which formats are supported."
                     .format(format_name, parser.prog))


def get_reader_by_extension(file_extension):
    for entry_point, dist in find_entry_points('rinoh.frontends'):
        reader_cls = entry_point.load()
        if file_extension in reader_cls.extensions:
            print('Using the {} frontend [{}]'
                  .format(entry_point.name, get_distribution_name(dist)))
            return entry_point.name, reader_cls
    print("Cannot determine input format from extension '{}'; assuming "
          "reStructuredText. You can specify the format using the `--format` "
          "option. Run `{} --list-formats` to find out which formats are "
          "supported.".format(file_extension, parser.prog))
    (entry_point, _), = find_entry_points('rinoh.frontends', 'reStructuredText')
    return entry_point.name, entry_point.load()


def installed_typefaces():
    for entry_point, dist in find_entry_points('rinoh.typefaces'):
        yield entry_point.load(), get_distribution_name(dist)
    for typeface in installed_google_fonts_typefaces():
        yield typeface, 'Google Fonts'


def display_fonts(filename):
    def font_paragraph(typeface, font):
        style = ParagraphStyle(typeface=typeface, font_width=font.width,
                               font_slant=font.slant, font_weight=font.weight)
        return Paragraph(' '.join((typeface.name,
                                   FontWidth.to_name(font.width).title(),
                                   font.slant.title(),
                                   FontWeight.to_name(font.weight).title())),
                         style=style)

    def typeface_section(typeface, distribution):
        group_style = GroupedFlowablesStyle(space_below=10*PT)
        title_style = ParagraphStyle(keep_with_next=True,
                                     tab_stops=[TabStop(100*PERCENT, 'right')],
                                     border_bottom=Stroke(0.5*PT, BLACK),
                                     padding_bottom=1*PT,
                                     space_below=2*PT)
        title = Paragraph('{}\t[{}]'.format(typeface.name, distribution),
                          style=title_style)
        return StaticGroupedFlowables([title]
                                      + [font_paragraph(typeface, font)
                                         for font in typeface.fonts()],
                                      style=group_style)

    document_tree = DocumentTree(typeface_section(typeface, dist)
                                 for typeface, dist in installed_typefaces())
    template_cfg = Article.Configuration('fonts overview', parts=['contents'])
    document = template_cfg.document(document_tree)
    document.render(filename)


def main():
    global parser
    args = parser.parse_args()
    do_exit = False
    if args.versions:
        _handle_versions()
        return
    if args.docs:
        webbrowser.open(DOCS_URL)
        return
    if args.list_templates:
        _handle_templates()
        do_exit = True
    if args.list_stylesheets:
        _handle_stylesheets()
        do_exit = True
    if args.list_formats:
        _handle_formats()
        do_exit = True
    if args.list_options:
        _handle_list_options(args)
        do_exit = True
    if args.list_fonts:
        if args.list_fonts is object:
            _handle_fonts()
        else:
            display_fonts(args.list_fonts)
        do_exit = True
    if do_exit:
        return

    if args.input is None:
        parser.print_help()
        return

    template_cfg = {}
    variables = {}
    cwd_source = CwdSource()
    _handle_stylesheet(args, cwd_source, parser, template_cfg)
    if args.paper:
        _handle_paper(args, variables)

    if not os.path.exists(args.input):
        raise SystemExit('{}: No such file'.format(args.input))
    input_dir, input_filename = os.path.split(args.input)
    input_root, input_ext = os.path.splitext(input_filename)

    output_path = set_ouput_path(args, input_root)

    reader_name, reader_cls = (get_reader_by_name(args.format) if args.format
                               else get_reader_by_extension(input_ext[1:]))
    str_options = dict((part.strip() for part in option.split('=', maxsplit=1))
                       for option, in args.option)
    options = _build_options(reader_cls, reader_name, str_options)
    reader = reader_cls(**options)

    template_cls = set_template(args, cwd_source, parser, template_cfg)

    configuration = template_cls.Configuration('rinoh command line options',
                                               **template_cfg)
    configuration.variables.update(variables)

    document_tree = reader.parse(args.input)
    _do_rendering(args, configuration, document_tree, output_path, template_cls)


def _handle_stylesheet(args, cwd_source, parser, template_cfg):
    if args.stylesheet:
        try:
            stylesheet = StyleSheet.from_string(args.stylesheet,
                                                source=cwd_source)
        except FileNotFoundError:
            raise SystemExit("Could not find the style sheet '{}'. "
                             "Aborting.\n"
                             "Make sure the path to your style sheet is "
                             "correct, or run `{} --list-stylesheets` to find "
                             "out which style sheets are installed."
                             .format(args.stylesheet, parser.prog))
        template_cfg['stylesheet'] = stylesheet


def _do_rendering(args, configuration, document_tree, output_path, template_cls):
    while True:
        try:
            document = template_cls(document_tree, configuration=configuration)
            success = document.render(output_path)
            if not success:
                raise SystemExit('Rendering completed with errors')
            break
        except ResourceNotFound as err:
            if args.install_resources:
                print("Attempting to the install the '{}' {} from PyPI:"
                      .format(err.resource_name, err.resource_type.title()))
                success = Typeface.install_from_pypi(err.entry_point_name)
                if not success:
                    raise SystemExit("No '{}' {} found on PyPI. Aborting."
                                     .format(err.resource_name,
                                             err.resource_type))
            else:
                raise SystemExit("{} '{}' not installed. Consider passing the "
                                 "--install-resources command line option."
                                 .format(err.resource_type.title(),
                                         err.resource_name))


def set_template(args, cwd_source, parser, template_cfg):
    if os.path.isfile(args.template):
        template_cfg['base'] = TemplateConfigurationFile(args.template,
                                                         source=cwd_source)
        template_cls = template_cfg['base'].template
    else:
        try:
            template_cls = DocumentTemplate.from_string(args.template)
        except ResourceNotFound:
            raise SystemExit("Could not find the template (configuration file) "
                             "'{}'. Aborting.\nMake sure the path to your "
                             "template configuration file is correct, or run "
                             "`{} --list-stylesheets` to find out which "
                             "templates are installed.".format(args.template,
                                                               parser.prog))
    return template_cls


def _build_options(reader_cls, reader_name, str_options):
    try:
        options = {}
        for key, str_value in str_options.items():
            attr_def = reader_cls.attribute_definition(key)
            options[key] = attr_def.accepted_type.from_string(str_value)
    except KeyError as e:
        raise SystemExit('The {} frontend does not accept the option {}'
                         .format(reader_name, e))
    except ValueError as e:
        raise SystemExit("The value passed to the '{}' option is not valid:\n"
                         '  {}'.format(key, e))
    return options


def set_ouput_path(args, input_root):
    if args.output:
        if os.path.isdir(args.output):
            output_path = os.path.join(args.output, input_root)
        else:
            output_path = args.output
    else:
        output_path = input_root
    return output_path


def _handle_paper(args, variables):
    try:
        variables['paper_size'] = Paper.from_string(args.paper.lower())
    except ValueError:
        accepted = ', '.join(sorted(paper.name for paper
                                    in PAPER_BY_NAME.values()))
        raise SystemExit("Unknown paper size '{}'. Must be one of:\n"
                         "   {}".format(args.paper, accepted))


def _handle_fonts():
    print('Installed fonts:')
    for typeface, distribution in installed_typefaces():
        print('- {} [{}]'.format(typeface.name, distribution))
        widths = OrderedDict()
        for font in typeface.fonts():
            widths.setdefault(font.width, []).append(font)
        for width, fonts in widths.items():
            styles = []
            for font in fonts:
                style = FontWeight.to_name(font.weight)
                if font.slant != FontSlant.UPRIGHT:
                    style = '{}-{}'.format(font.slant, style)
                styles.append(style)
            print('   {}: {}'.format(FontWidth.to_name(width),
                                     ', '.join(styles)))


def _handle_list_options(args):
    reader_name, reader_cls = get_reader_by_name(args.list_options)
    if list(reader_cls.supported_attributes):
        print('Options supported by the {} frontend'.format(reader_name))
        for name in reader_cls.supported_attributes:
            attr_def = reader_cls.attribute_definition(name)
            print('- {} ({}): {}. Default: {}'
                  .format(name, attr_def.accepted_type.__name__,
                          attr_def.description, attr_def.default_value))
    else:
        print('The {} frontend takes no options'.format(reader_name))


def _handle_formats():
    print('Supported input file formats:')
    for entry_point, dist in find_entry_points('rinoh.frontends'):
        reader_cls = entry_point.load()
        print('- {} (.{}) [{}]'
              .format(entry_point.name, ', .'.join(reader_cls.extensions),
                      get_distribution_name(dist)))


def _handle_stylesheets():
    print('Installed style sheets:')
    for name, _ in sorted(StyleSheet.installed_resources):
        print('- {}'.format(name))


def _handle_templates():
    print('Installed document templates:')
    for name, _ in sorted(DocumentTemplate.installed_resources):
        print('- {}'.format(name))


def _handle_versions():
    print(f'rinohtype {__version__} ({__release_date__})')
    with suppress(ImportError):
        import sphinx
        print(f'Sphinx {sphinx.__version__}')
    print(f'Python {sys.version}')
    print(platform())


class CwdSource(Source):
    @property
    def location(self):
        return 'current working directory'

    @property
    def root(self):
        return Path.cwd()


if __name__ == '__main__':
    main()
