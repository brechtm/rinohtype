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

SPHINX_DOC_DIR = TEST_DIR / 'sphinx' / 'doc'


@pytest.mark.longrunning
def test_sphinxdocs(tmpdir):
    template_cfg_path = TEST_DIR / 'sphinxdocs.rtt'
    sphinx = Sphinx(srcdir=str(SPHINX_DOC_DIR),
                    confdir=str(SPHINX_DOC_DIR),
                    outdir=tmpdir.join('rinoh').strpath,
                    doctreedir=tmpdir.join('doctrees').strpath,
                    buildername='rinoh',
                    confoverrides=dict(rinoh_template=str(template_cfg_path)))
    sphinx.build()

    out_file = tmpdir.join('rinoh').join('sphinx.pdf').strpath
    with in_directory(tmpdir.strpath):
        if not diff_pdf(TEST_DIR / 'reference' / 'sphinx.pdf', out_file):
            pytest.fail('The generated PDF is different from the reference '
                        'PDF.\nGenerated files can be found in {}'
                        .format(tmpdir.strpath))
