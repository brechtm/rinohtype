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

from rinoh.frontend.rst import ReStructuredTextReader, from_doctree
from rinoh.frontend.sphinx import nodes    # load Sphinx docutils nodes
from rinoh.attribute import OverrideDefault, Var
from rinoh.template import (DocumentTemplate, TemplateConfiguration,
                            ContentsPartTemplate, PageTemplate,
                            TemplateConfigurationFile)


__all__ = ['render_doctree', 'render_rst_file']


TEST_DIR = Path(__file__).parent.parent.absolute()
OUTPUT_DIR = TEST_DIR / 'output'

class MinimalTemplate(DocumentTemplate):
    stylesheet = OverrideDefault('sphinx_base14')
    parts = OverrideDefault(['contents'])
    contents = ContentsPartTemplate()
    page = PageTemplate(page_size=Var('paper_size'),
                        chapter_title_flowables=None,
                        header_text=None,
                        footer_text=None)
    contents_page = PageTemplate(base='page')


def _render_rst(rst_path, doctree, out_filename, reference_path, warnings=[]):
    kwargs = {}
    stylesheet_path = rst_path.with_suffix('.rts')
    if stylesheet_path.exists():
        kwargs['stylesheet'] = str(stylesheet_path)
    templconf_path = rst_path.with_suffix('.rtt')
    if templconf_path.exists():
        config = TemplateConfigurationFile(str(templconf_path))
    else:
        config = TemplateConfiguration('rst', template=MinimalTemplate, **kwargs)
        config.variables['paper_size'] = 'a5'
    render_doctree(doctree, out_filename, reference_path, config, warnings)


def render_rst_file(rst_path, out_filename, reference_path):
    reader = ReStructuredTextReader()
    doctree = reader.parse(rst_path)
    return _render_rst(rst_path, doctree, out_filename, reference_path)


def render_sphinx_rst_file(rst_path, out_filename, reference_path,
                           test_output_dir):
    with docutils_namespace():
        out_dir = str(test_output_dir)
        app = Sphinx(srcdir=str(rst_path.parent), confdir=None, outdir=out_dir,
                     doctreedir=out_dir, buildername='dummy', status=None)
        with open(rst_path) as rst_file:
            contents = rst_file.read()
        sphinx_doctree = sphinx_parse(app, contents)
    doctree = from_doctree(rst_path.name, sphinx_doctree)
    docinfo = sphinx_doctree.settings.env.metadata['index']
    return _render_rst(rst_path, doctree, out_filename, reference_path,
                       warnings=docinfo.get('warnings', '').splitlines())


def render_doctree(doctree, out_filename, reference_path,
                   template_configuration=None, warnings=[]):
    if template_configuration:
        document = template_configuration.document(doctree)
    else:
        document = MinimalTemplate(doctree)
    output_dir = OUTPUT_DIR / out_filename
    output_dir.mkdir(parents=True, exist_ok=True)
    with pytest.warns(None) as recorded_warnings:
        document.render(output_dir / out_filename)
    if 'warnings' in document.metadata:
        warnings_node = document.metadata['warnings'].source.node
        warnings = chain(warnings_node.rawsource.splitlines(), warnings)
    for warning in warnings:
        if not any(re.search(warning, str(w.message)) for w in recorded_warnings):
            pytest.fail('Expected warning matching "{}"'.format(warning))
    verify_output(out_filename, output_dir, reference_path)


def render_sphinx_project(name, project_dir, template_cfg=None):
    project_path = TEST_DIR / project_dir
    out_path = OUTPUT_DIR / name
    confoverrides = {}
    if template_cfg:
        confoverrides['rinoh_template'] = str(TEST_DIR / template_cfg)
    with docutils_namespace():
        sphinx = Sphinx(srcdir=str(project_path),
                        confdir=str(project_path),
                        outdir=str(out_path / 'rinoh'),
                        doctreedir=str(out_path / 'doctrees'),
                        buildername='rinoh',
                        confoverrides=confoverrides)
        sphinx.build()
    out_filename = '{}.pdf'.format(name)
    with in_directory(out_path):
        if not diff_pdf(TEST_DIR / 'reference' / out_filename,
                        out_path / 'rinoh' / out_filename):
            pytest.fail('The generated PDF is different from the reference '
                        'PDF.\nGenerated files can be found in {}'
                        .format(out_path))


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
