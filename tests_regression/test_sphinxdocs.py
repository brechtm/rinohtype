# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


import os

import pytest

from diffpdf import diff_pdf
from pdf_linkchecker import check_pdf_links
from util import in_directory

from rinoh.strings import Strings
from rinoh.structure import AdmonitionTitles
from rinoh.templates import Book

TEST_DIR = os.path.abspath(os.path.dirname(__file__))

SPHINX_DOC_DIR = os.path.join(TEST_DIR, 'sphinx', 'doc')


def test_sphinxdocs(tmpdir):
    from sphinx.application import Sphinx

    strings = Strings(AdmonitionTitles(error='Error:',
                                       hint='Hint:',
                                       important='Important',
                                       note='Note:',
                                       tip='Tip:',
                                       warning='Warning:',
                                       seealso='See also:'))
    template_configuration = Book.Configuration('Sphinx test',
                                                strings=strings)
    template_configuration('title_page', show_date=False)

    sphinx = Sphinx(srcdir=SPHINX_DOC_DIR,
                    confdir=SPHINX_DOC_DIR,
                    outdir=tmpdir.join('rinoh').strpath,
                    doctreedir=tmpdir.join('doctrees').strpath,
                    buildername='rinoh',
                    confoverrides=dict(extensions=['sphinx.ext.autodoc',
                                                   'sphinx.ext.doctest',
                                                   'sphinx.ext.todo',
                                                   'sphinx.ext.autosummary',
                                                   'sphinx.ext.extlinks',
                                                   'sphinx.ext.viewcode',
                                                   'rinoh.frontend.sphinx'],
                                       rinoh_template_configuration=
                                           template_configuration))
    sphinx.build()

    out_file = tmpdir.join('rinoh').join('sphinx.pdf').strpath
    with in_directory(tmpdir.strpath):
        # _, _, _, badlinks, _, _ = check_pdf_links(out_file)
        # pytest.assume(badlinks == [], 'Output PDF contains broken '
        #                               'hyperlinks: {}'.format(badlinks))
        if not diff_pdf(os.path.join(TEST_DIR, 'reference/sphinx.pdf'),
                        out_file):
            pytest.fail('The generated PDF is different from the reference '
                        'PDF.\nGenerated files can be found in {}'
                        .format(tmpdir.strpath))
