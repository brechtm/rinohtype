# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.

import pytest

import tempfile

from io import BytesIO
from os import path

from diffpdf import diff_pdf
from pdf_linkchecker import check_pdf_links
from util import in_directory

from sphinx.application import Sphinx

from rinoh.attribute import OverrideDefault, Var
from rinoh.frontend.rst import ReStructuredTextReader
from rinoh.frontend.sphinx import nodes    # load the Sphinx docutils nodes
from rinoh.template import DocumentTemplate, ContentsPartTemplate, PageTemplate


TEST_DIR = path.abspath(path.dirname(__file__))


class Minimal(DocumentTemplate):
    variables = dict(paper_size='a5')

    stylesheet = OverrideDefault('sphinx_base14')
    parts = OverrideDefault(['contents'])
    contents = ContentsPartTemplate()
    page = PageTemplate(page_size=Var('paper_size'),
                        chapter_title_flowables=None)
    contents_page = PageTemplate(base='page')


def render(source, filename):
    file = BytesIO('\n'.join(source).encode('utf-8'))
    reader = ReStructuredTextReader()
    doctree = reader.parse(file)
    document = Minimal(doctree)
    tmpdir = tempfile.mkdtemp()
    document.render(path.join(tmpdir, filename))
    pdf_filename = '{}.pdf'.format(filename)
    with in_directory(tmpdir):
        # register Sphinx directives and roles
        Sphinx(srcdir=tmpdir, confdir=None, outdir=tmpdir, doctreedir=tmpdir,
               buildername='dummy', status=None)
        _, _, _, badlinks, _, _ = check_pdf_links(pdf_filename)
        pytest.assume(badlinks == [])
        if not diff_pdf(path.join(TEST_DIR, 'reference', pdf_filename),
                        pdf_filename):
            pytest.fail('The generated PDF is different from the reference '
                        'PDF.\nGenerated files can be found in {}'
                        .format(tmpdir))


def test_centered():
    source = ('.. centered:: A centered paragraph.')
    render(source, 'centered')


def test_hlist():
    source = ('.. hlist::',
              '   :columns: 3',
              '',
              '   * A list of',
              '   * short items',
              '   * that should be',
              '   * displayed',
              '   * horizontally')
    render(source, 'hlist')


def test_inline_markup():
    source = ('Inline Markup roles:',
              '',
              ':abbr:          :abbr:`LIFO (last-in, first-out)` :abbr:`KISS`',
              ':command:       :command:`rm`',
              ':dfn:           :dfn:`definition`',
              ':file:          :file:`README.txt` :file:`Makefile`',
              ':guilabel:      :guilabel:`&Cancel`',
              ':kbd:           :kbd:`Control-x`',
              ':mailheader:    :mailheader:`Content-Type`',
              ':makevar:       :makevar:`var`',
              ':manpage:       :manpage:`ls(1)`',
              ':menuselection: :menuselection:`Menu --> Item`',
              ':mimetype:      :mimetype:`png`',
              ':newsgroup:     :newsgroup:`comp.lang.python`',
              ':program:       :program:`rinoh`',
              ':regexp:        :regexp:`.*`',
              ':samp:          :samp:`print 1+{variable}`')
    render(source, 'inline_markup')
