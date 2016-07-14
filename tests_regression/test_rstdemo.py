# This file is part of RinohType, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


import os
import pytest
import subprocess

from pdf_linkchecker import check_pdf_links

from rinoh.backend import pdf
from rinoh.dimension import CM
from rinoh.frontend.rst import ReStructuredTextReader
from rinoh.stylesheets import sphinx_base14
from rinoh.templates import Article


TEST_DIR = os.path.abspath(os.path.dirname(__file__))

DIFF_PDF = os.path.join(TEST_DIR, 'diffpdf.sh')


def test_rstdemo(tmpdir, expect):
    configuration = Article.Configuration(stylesheet=sphinx_base14,
                                          abstract_location='title',
                                          table_of_contents=False)
    configuration('title_page', top_margin=2*CM)

    with open(os.path.join(TEST_DIR, 'demo.txt')) as file:
        parser = ReStructuredTextReader()
        flowables = parser.parse(file)
    document = Article(flowables, configuration=configuration, backend=pdf)
    os.chdir(tmpdir.strpath)
    document.render('demo')
    _, _, _, badlinks, _, _ =check_pdf_links('demo.pdf')
    expect(badlinks == ['table-of-contents'])
    if not diff_pdf(os.path.join(TEST_DIR, 'reference/demo.pdf'), 'demo.pdf'):
        pytest.fail('The generated PDF is different from the reference PDF.\n'
                    'Generated files can be found in {}'.format(tmpdir.strpath))


def diff_pdf(a_filename, b_filename):
    rc = subprocess.call([DIFF_PDF, a_filename, b_filename])
    return rc == 0
