# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.

import pytest
import re

from itertools import chain
from pathlib import Path

from sphinx.application import Sphinx
from sphinx.util.docutils import docutils_namespace
from sphinx.testing.restructuredtext import parse as sphinx_parse

from .diffpdf import diff_pdf
from .pdf_linkchecker import check_pdf_links
from .util import in_directory

from rinoh.frontend.commonmark import CommonMarkReader
from rinoh.frontend.rst import ReStructuredTextReader, from_doctree
from rinoh.frontend.sphinx import nodes    # load Sphinx docutils nodes
from rinoh.attribute import OverrideDefault, Var
from rinoh.template import (DocumentTemplate, TemplateConfiguration,
                            ContentsPartTemplate, PageTemplate,
                            TemplateConfigurationFile)


__all__ = ['render_doctree', 'render_md_file', 'render_rst_file']


TEST_DIR = Path(__file__).parent.parent.absolute()


class MinimalTemplate(DocumentTemplate):
    stylesheet = OverrideDefault('sphinx_base14')
    parts = OverrideDefault(['contents'])
    contents = ContentsPartTemplate()
    page = PageTemplate(page_size=Var('paper_size'),
                        chapter_title_flowables=None,
                        header_text=None,
                        footer_text=None)
    contents_page = PageTemplate(base='page')


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
    with pytest.warns(None) as recorded_warnings:
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
    _, _, _, _, _, _, ref_outlines = \
        check_pdf_links(reference_path / pdf_filename)
    with in_directory(output_dir):
        _, _, _, badlinks, _, _, outlines = check_pdf_links(pdf_filename)
        pytest.assume(badlinks == [])
        pytest.assume(ref_outlines == outlines)
        if not diff_pdf(reference_path / pdf_filename, pdf_filename):
            pytest.fail('The generated PDF is different from the reference '
                        'PDF.\nGenerated files can be found in {}'
                        .format(output_dir))
