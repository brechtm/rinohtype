# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.

import pytest

from pathlib import Path

import sphinx

from .helpers.regression import render_rst_file, render_sphinx_rst_file


RST_PATH = Path(__file__).parent / 'rst'

SPHINX_MIN_MAX_VERSION = {  # min=inclusive, max=exclusive
    'sphinx_admonition': ('7.3', None),
    'sphinx_collapsible': ('8.2', None),
    'sphinx_inline_markup': ('3.2', '8.2'),
    'sphinx_domain': ('7.1', None),
}


def version_to_tuple(version):
    return tuple(int(v) for v in version.split('.'))


def collect_tests():
    for rst_path in sorted(RST_PATH.glob('*.rst')):
        marks = []
        try:
            min_ver, max_ver = SPHINX_MIN_MAX_VERSION[rst_path.stem]
        except KeyError:
            pass
        else:
            if min_ver and sphinx.version_info < version_to_tuple(min_ver):
                reason = f"minimum Sphinx version is {min_ver}"
            elif max_ver and sphinx.version_info >= version_to_tuple(max_ver):
                reason = f"maximum Sphinx version is {max_ver}"
            else:
                reason = None
            if reason:
                marks.append(pytest.mark.skip(reason))
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
