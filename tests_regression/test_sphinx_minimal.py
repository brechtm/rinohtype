# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.

import pytest

from pathlib import Path

from diffpdf import diff_pdf
from util import in_directory

from sphinx.application import Sphinx


TEST_DIR = Path(__file__).parent

SPHINX_MINIMAL_DIR = TEST_DIR / 'sphinx_minimal'


def test_sphinxdocs(tmpdir):
    sphinx = Sphinx(srcdir=str(SPHINX_MINIMAL_DIR),
                    confdir=str(SPHINX_MINIMAL_DIR),
                    outdir=tmpdir.join('rinoh').strpath,
                    doctreedir=tmpdir.join('doctrees').strpath,
                    buildername='rinoh')
    sphinx.build()

    out_file = tmpdir.join('rinoh').join('sphinx_minimal.pdf').strpath
    with in_directory(tmpdir.strpath):
        reference_pdf = TEST_DIR / 'reference' / 'sphinx_minimal.pdf'
        if not diff_pdf(reference_pdf, out_file):
            pytest.fail('The generated PDF is different from the reference '
                        'PDF.\nGenerated files can be found in {}'
                        .format(tmpdir.strpath))
