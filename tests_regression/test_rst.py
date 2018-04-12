# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.

import pytest

from pathlib import Path

from regression import render_rst_file


RST_PATH = Path(__file__).parent / 'rst'


def collect_tests():
    for rst_path in RST_PATH.glob('*.rst'):
        yield rst_path.stem


@pytest.mark.parametrize('test_name', collect_tests())
def test(test_name, tmpdir):
    rst_path = RST_PATH / (test_name + '.rst')
    if test_name.startswith('sphinx_'):
        from sphinx.application import Sphinx
        from rinoh.frontend.sphinx import nodes    # load Sphinx docutils nodes

        Sphinx(srcdir=tmpdir.strpath, confdir=None, outdir=tmpdir.strpath,
               doctreedir=tmpdir.strpath, buildername='dummy', status=None)
    render_rst_file(rst_path, test_name, RST_PATH, tmpdir)
