# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.

import pytest

from pathlib import Path

import sphinx

from helpers.regression import render_rst_file, render_sphinx_rst_file


RST_PATH = Path(__file__).parent / 'rst'

MIN_SPHINX_VERSION = {
    'sphinx_inline_markup': '3.2',
}


def collect_tests():
    for rst_path in sorted(RST_PATH.glob('*.rst')):
        marks = []
        try:
            version = MIN_SPHINX_VERSION[rst_path.stem]
            skip = sphinx.version_info < tuple(map(int, version.split('.')))
            reason = "minimum Sphinx version is " + '.'.join(version)
            marks.append(pytest.mark.skipif(skip, reason=reason))
        except KeyError:
            pass
        if rst_path.stem.startswith('sphinx_'):
            marks.append(pytest.mark.with_sphinx)
        yield pytest.param(rst_path.stem, marks=marks)


@pytest.mark.parametrize('test_name', collect_tests())
def test_rst(test_name):
    rst_path = RST_PATH / (test_name + '.rst')
    if test_name.startswith('sphinx_'):
        render_sphinx_rst_file(rst_path, test_name, RST_PATH)
    else:
        render_rst_file(rst_path, test_name, RST_PATH)
