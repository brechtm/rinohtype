# This file is part of RinohType, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


import pytest

import os
import subprocess

from rinoh.backend import pdf
from rinoh.dimension import CM
from rinoh.frontend.rst import ReStructuredTextReader
from rinoh.stylesheets import sphinx_base14
from rinoh.template import DocumentOptions
from rinoh.templates import Article


TEST_DIR = os.path.abspath(os.path.dirname(__file__))

DIFF_PDF = os.path.join(TEST_DIR, 'diffpdf.sh')


def test_rstdemo(tmpdir):
    configuration = Article.Configuration()
    configuration.abstract_location('title')
    configuration.table_of_contents(False)
    configuration.title_page(top_margin=2 * CM)

    with open(os.path.join(TEST_DIR, 'demo.txt')) as file:
        parser = ReStructuredTextReader()
        flowables = parser.parse(file)
    options = DocumentOptions(stylesheet=sphinx_base14)
    document = Article(flowables, configuration=configuration,
                       options=options, backend=pdf)
    output = tmpdir.join('demo').strpath
    document.render(output)
    os.chdir(tmpdir.strpath)
    print('CWD: ', os.getcwd())
    print(os.path.join(TEST_DIR, 'reference/demo.pdf'))
    print(output + '.pdf')
    diff_pdf(os.path.join(TEST_DIR, 'reference/demo.pdf'),
             output + '.pdf')


def diff_pdf(a_filename, b_filename):
    rc = subprocess.call([DIFF_PDF, a_filename, b_filename])
    if rc != 0:
        pytest.fail('The generated PDF is different from the reference PDF.')
