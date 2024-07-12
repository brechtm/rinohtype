# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.

import pytest
import re

from itertools import chain, zip_longest
from pathlib import Path
from warnings import catch_warnings

from sphinx.application import Sphinx
from sphinx.util.docutils import docutils_namespace
from sphinx.testing.restructuredtext import parse as sphinx_parse

from .diffpdf import diff_pdf
from .pdf_linkchecker import check_pdf_links, diff_outlines
from .util import in_directory

from rinoh import register_template
from rinoh.attribute import OverrideDefault, Var
from rinoh.dimension import CM
from rinoh.frontend.commonmark import CommonMarkReader
from rinoh.frontend.rst import ReStructuredTextReader, from_doctree
from rinoh.frontend.sphinx import nodes    # load Sphinx docutils nodes
from rinoh.structure import TableOfContentsSection
from rinoh.template import (DocumentTemplate, TemplateConfiguration,
                            ContentsPartTemplate, BodyPageTemplate,
                            TemplateConfigurationFile, TitlePageTemplate,
                            TitlePartTemplate, DocumentPartTemplate)


__all__ = ['render_doctree', 'render_md_file', 'render_rst_file',
           'verify_output']


TEST_DIR = Path(__file__).parent.parent.absolute()


class MinimalTemplate(DocumentTemplate):
    stylesheet = OverrideDefault('sphinx_base14')
    parts = OverrideDefault(['contents'])
    contents = ContentsPartTemplate()
    page = BodyPageTemplate(page_size=Var('paper_size'),
                            chapter_title_flowables=None,
                            header_text=None,
                            footer_text=None)
    contents_page = BodyPageTemplate(base='page')


register_template('minimal', MinimalTemplate)


class MinimalFrontMatter(DocumentPartTemplate):
    toc_section = TableOfContentsSection()

    def _flowables(self, document):
        yield self.toc_section


class MinimalSphinxTemplate(DocumentTemplate):
    stylesheet = OverrideDefault('sphinx_base14')
    parts = OverrideDefault(['title', 'front_matter', 'contents'])

    title = TitlePartTemplate()
    front_matter = MinimalFrontMatter(page_number_format='continue')
    contents = ContentsPartTemplate(page_number_format='continue')

    page = BodyPageTemplate(page_size=Var('paper_size'))
    title_page = TitlePageTemplate(base='page',
                                   top_margin=8*CM)
    front_matter_page = BodyPageTemplate(base='page')
    contents_page = BodyPageTemplate(base='page')


register_template('minimal_sphinx', MinimalSphinxTemplate)


def render_md_file(md_path, out_filename, reference_path):
    reader = CommonMarkReader()
    doctree = reader.parse(md_path)
    return _render_file(md_path, doctree, TEST_DIR / 'md_output',
                        out_filename, reference_path)


def render_rst_file(rst_path, out_filename, reference_path):
    reader = ReStructuredTextReader()
    doctree = reader.parse(rst_path)
    return _render_file(rst_path, doctree, TEST_DIR / 'rst_output',
                        out_filename, reference_path)


def render_sphinx_rst_file(rst_path, out_filename, reference_path):
    output_dir = TEST_DIR / 'rst_output'
    with docutils_namespace():
        out_dir = str(output_dir / out_filename)
        app = Sphinx(srcdir=str(rst_path.parent), confdir=None, outdir=out_dir,
                     doctreedir=out_dir, buildername='dummy', status=None)
        with open(rst_path) as rst_file:
            contents = rst_file.read()
        sphinx_doctree = sphinx_parse(app, contents)
    doctree = from_doctree(sphinx_doctree)
    docinfo = sphinx_doctree.settings.env.metadata['index']
    warnings = docinfo.get('warnings', '').splitlines()
    return _render_file(rst_path, doctree, output_dir, out_filename,
                        reference_path, warnings=warnings)


def _render_file(file_path, doctree, out_dir, out_filename, reference_path,
                 warnings=[]):
    kwargs = {}
    stylesheet_path = file_path.with_suffix('.rts')
    if stylesheet_path.exists():
        kwargs['stylesheet'] = str(stylesheet_path)
    templconf_path = file_path.with_suffix('.rtt')
    if templconf_path.exists():
        config = TemplateConfigurationFile(str(templconf_path))
    else:
        config = TemplateConfiguration('rst', template=MinimalTemplate,
                                       **kwargs)
        config.variables['paper_size'] = 'a5'
    render_doctree(doctree, out_dir, out_filename, reference_path, config,
                   warnings)


def render_doctree(doctree, out_dir, out_filename, reference_path,
                   template_configuration=None, warnings=[]):
    if template_configuration:
        document = template_configuration.document(doctree)
    else:
        document = MinimalTemplate(doctree)
    output_dir = out_dir / out_filename
    output_dir.mkdir(parents=True, exist_ok=True)
    with catch_warnings(record=True) as recorded_warnings:
        document.render(output_dir / out_filename)
    if 'warnings' in document.metadata:
        warnings_node = document.metadata['warnings'].source.node
        warnings = chain(warnings_node.rawsource.splitlines(), warnings)
    for warning in warnings:
        if not any(re.search(warning, str(w.message))
                   for w in recorded_warnings):
            pytest.fail('Expected warning matching "{}"'.format(warning))
    verify_output(out_filename, output_dir, reference_path)


def verify_output(out_filename, output_dir, reference_path):
    pdf_filename = '{}.pdf'.format(out_filename)
    _, _, _, _, _, _, _, ref_outlines = \
        check_pdf_links(reference_path / pdf_filename)
    with in_directory(output_dir):
        _, _, _, badlinks, badoutlinelinks, _, _, outlines = \
            check_pdf_links(pdf_filename)
        pytest.assume(badlinks == [], badlinks)
        pytest.assume(badoutlinelinks == [], badoutlinelinks)
        pytest.assume(diff_outlines(ref_outlines, outlines),
                      "Outlines mismatch!          (ref | new)\n"
                      + format_outlines(ref_outlines, outlines))
        if not diff_pdf(reference_path / pdf_filename, pdf_filename):
            pytest.fail('The generated PDF is different from the reference '
                        'PDF.\nGenerated files can be found in {}'
                        .format(output_dir))


def format_outlines(reference, outlines):
    return '\n'.join(f"{'':<{l1 - 1}}{title1!s:{25 - l1}} {id1!s:20}  |  "
                     f"{'':<{l2 - 1}}{title2!s:{25 - l2}} {id2!s:20}"
                     for (l1, title1, id1), (l2, title2, id2)
                     in zip_longest(reference, outlines, fillvalue=(1, '', '')))
