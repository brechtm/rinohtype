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
from regression import TEST_DIR, OUTPUT_DIR
from util import in_directory

from rinoh.frontend.rst import ReStructuredTextReader
from rinoh.template import TemplateConfigurationFile


@pytest.mark.longrunning
def test_rstdemo():
    config = TemplateConfigurationFile(TEST_DIR / 'rstdemo.rtt')

    parser = ReStructuredTextReader()
    flowables = parser.parse(TEST_DIR / 'demo.txt')
    document = config.document(flowables)
    out_dir = OUTPUT_DIR / 'rstdemo'
    out_dir.mkdir(parents=True, exist_ok=True)
    with in_directory(out_dir):
        document.render('demo')
        _, _, _, badlinks, _, _ = check_pdf_links('demo.pdf')
        pytest.assume(badlinks == ['table-of-contents'])
        if not diff_pdf(TEST_DIR / 'reference' / 'demo.pdf', 'demo.pdf'):
            pytest.fail('The generated PDF is different from the reference '
                        'PDF.\nGenerated files can be found in {}'
                        .format(out_dir))
