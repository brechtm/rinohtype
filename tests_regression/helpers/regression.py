# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.

import pytest

from pathlib import Path

from diffpdf import diff_pdf
from pdf_linkchecker import check_pdf_links
from util import in_directory

from rinoh.frontend.rst import ReStructuredTextReader
from rinoh.attribute import OverrideDefault, Var
from rinoh.template import (DocumentTemplate, TemplateConfiguration,
                            ContentsPartTemplate, PageTemplate)


__all__ = ['render_doctree', 'render_rst_file']


TEST_DIR = Path(__file__).parent.parent.absolute()


class MinimalTemplate(DocumentTemplate):
    variables = dict(paper_size='a5')

    stylesheet = OverrideDefault('sphinx_base14')
    parts = OverrideDefault(['contents'])
    contents = ContentsPartTemplate()
    page = PageTemplate(page_size=Var('paper_size'),
                        chapter_title_flowables=None,
                        header_text=None,
                        footer_text=None)
    contents_page = PageTemplate(base='page')


def render_rst_file(rst_path, out_filename, reference_path, tmpdir):
    reader = ReStructuredTextReader()
    doctree = reader.parse(rst_path)
    stylesheet_path = rst_path.with_suffix('.rts')
    config = (TemplateConfiguration('rst', template=MinimalTemplate,
                                    stylesheet=str(stylesheet_path))
              if stylesheet_path.exists() else None)
    render_doctree(doctree, out_filename, reference_path, tmpdir, config)


def render_doctree(doctree, out_filename, reference_path, tmpdir,
                   template_configuration=None):
    if template_configuration:
        document = template_configuration.document(doctree)
    else:
        document = MinimalTemplate(doctree)
    document.render(tmpdir.join(out_filename).strpath)
    output_dir = TEST_DIR / 'output' / out_filename
    if output_dir.is_symlink():
        output_dir.unlink()
    output_dir.symlink_to(tmpdir.strpath, target_is_directory=True)
    pdf_filename = '{}.pdf'.format(out_filename)
    with in_directory(tmpdir.strpath):
        _, _, _, badlinks, _, _ = check_pdf_links(pdf_filename)
        pytest.assume(badlinks == [])
        if not diff_pdf(reference_path / pdf_filename, pdf_filename):
            pytest.fail('The generated PDF is different from the reference '
                        'PDF.\nGenerated files can be found in {}'
                        .format(tmpdir.strpath))
