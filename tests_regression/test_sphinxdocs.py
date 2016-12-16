# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


import pytest

from os import path

from diffpdf import diff_pdf
from pdf_linkchecker import check_pdf_links
from util import in_directory

from sphinx.application import Sphinx

from rinoh.template import TemplateConfigurationFile


TEST_DIR = path.abspath(path.dirname(__file__))

SPHINX_DOC_DIR = path.join(TEST_DIR, 'sphinx', 'doc')


def test_sphinxdocs(tmpdir):
    template_cfg_path = path.join(TEST_DIR, 'sphinxdocs.rtt')
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
                                       rinoh_template=template_cfg_path))
    sphinx.build()

    out_file = tmpdir.join('rinoh').join('sphinx.pdf').strpath
    with in_directory(tmpdir.strpath):
        # _, _, _, badlinks, _, _ = check_pdf_links(out_file)
        # pytest.assume(badlinks == [], 'Output PDF contains broken '
        #                               'hyperlinks: {}'.format(badlinks))
        if not diff_pdf(path.join(TEST_DIR, 'reference/sphinx.pdf'), out_file):
            pytest.fail('The generated PDF is different from the reference '
                        'PDF.\nGenerated files can be found in {}'
                        .format(tmpdir.strpath))
