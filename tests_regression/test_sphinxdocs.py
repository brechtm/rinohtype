# This file is part of RinohType, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


import os

import pytest

from diffpdf import diff_pdf
from pdf_linkchecker import check_pdf_links


TEST_DIR = os.path.abspath(os.path.dirname(__file__))

SPHINX_DOC_DIR = os.path.join(TEST_DIR, 'sphinx', 'doc')


def test_sphinxdocs(tmpdir):
    from sphinx.application import Sphinx
    from rinoh.frontend.sphinx import setup as setup_rinoh_sphinx_builder

    sphinx = Sphinx(srcdir=SPHINX_DOC_DIR,
                    confdir=SPHINX_DOC_DIR,
                    outdir=tmpdir.join('rinoh').strpath,
                    doctreedir=tmpdir.join('doctrees').strpath,
                    buildername='html',
                    confoverrides=dict(extensions=['rinoh.frontend.sphinx']))
    setup_rinoh_sphinx_builder(sphinx)
    sphinx._init_builder('rinoh')
    sphinx.build()

    out_file = tmpdir.join('rinoh').join('sphinx.pdf').strpath
    os.chdir(tmpdir.strpath)
    # _, _, _, badlinks, _, _ = check_pdf_links(out_file)
    # pytest.assume(badlinks == [], 'Output PDF contains broken '
    #                               'hyperlinks: {}'.format(badlinks))
    if not diff_pdf(os.path.join(TEST_DIR, 'reference/sphinx.pdf'), out_file):
        pytest.fail('The generated PDF is different from the reference PDF.\n'
                    'Generated files can be found in {}'.format(tmpdir.strpath))
