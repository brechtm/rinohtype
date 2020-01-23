# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.

import pytest

from pathlib import Path

from sphinx.application import Sphinx
from sphinx.util.docutils import docutils_namespace

from rinoh.frontend.sphinx import nodes    # load Sphinx docutils nodes

from regression import render_rst_file, OUTPUT_DIR

RST_PATH = Path(__file__).parent / 'rst'


def collect_tests():
    for rst_path in sorted(RST_PATH.glob('*.rst')):
        yield rst_path.stem


@pytest.mark.parametrize('test_name', collect_tests())
def test(test_name):
    rst_path = RST_PATH / (test_name + '.rst')
    test_output_dir = OUTPUT_DIR / test_name
    if test_name.startswith('sphinx_'):
        with docutils_namespace():
            out_dir = str(test_output_dir)
            Sphinx(srcdir=str(RST_PATH), confdir=None, outdir=out_dir,
                   doctreedir=out_dir, buildername='dummy', status=None)
            render_rst_file(rst_path, test_name, RST_PATH)
    else:
        render_rst_file(rst_path, test_name, RST_PATH)

