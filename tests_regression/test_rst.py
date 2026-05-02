# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.

import pytest

from pathlib import Path

import sphinx

from docutils import nodes
from docutils.core import publish_doctree

from .helpers.regression import TIMEOUT, render_rst_file, render_sphinx_rst_file


RST_PATH = Path(__file__).parent / 'rst'


def version_to_tuple(version):
    """Convert a version string like '7.3' to a tuple like (7, 3)."""
    return tuple(int(v) for v in version.split('.'))


def parse_rst_metadata(rst_path):
    """Parse docinfo metadata fields from an RST file."""
    doctree = publish_doctree(rst_path.read_text(encoding='utf-8'),
                              source_path=str(rst_path),
                              settings_overrides={'report_level': 5})
    metadata = {}
    index = doctree.first_child_matching_class(nodes.docinfo)
    if index is not None:
        for field in doctree[index]:
            if isinstance(field, nodes.field):
                name = field[0].astext().lower()
                value = field[1].astext().strip()
                metadata[name] = value
    return metadata


def collect_tests():
    for rst_path in sorted(RST_PATH.glob('*.rst')):
        metadata = parse_rst_metadata(rst_path)
        marks = []
        timeout = int(metadata.get('timeout', TIMEOUT))
        marks.append(pytest.mark.timeout(timeout))
        min_ver = metadata.get('sphinx-minversion')
        max_ver = metadata.get('sphinx-maxversion')
        if min_ver or max_ver:
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
