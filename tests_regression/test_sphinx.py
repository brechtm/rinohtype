# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.

import pytest

import shutil
import sys

from contextlib import suppress
from pathlib import Path

import sphinx

from .helpers.regression import verify_output, version_to_tuple


TESTS_PATH = Path(__file__).parent
ROOTS_PATH = TESTS_PATH / 'sphinx'
OUTPUT_PATH = TESTS_PATH / 'sphinx_output'
OUTPUT_PATH.mkdir(exist_ok=True)


# run these tests only on specific platforms
PLATFORMS = {
    'graphviz': ('darwin'),
}

SPHINX_MIN_VERSION = {
    'pyref': '6.2'
}


def collect_tests():
    for root_path in sorted(ROOTS_PATH.glob('test-*')):
        test_name = root_path.stem.replace('test-', '')
        marks = [pytest.mark.sphinx(buildername='rinoh', testroot=test_name)]
        with suppress(KeyError):
            platforms = PLATFORMS[test_name]
            marks.append(pytest.mark.skipif(sys.platform not in platforms,
                                            reason='skipping test on '
                                                   f'{sys.platform}'))
        with suppress(KeyError):
            min_ver = SPHINX_MIN_VERSION[test_name]
            if sphinx.version_info < version_to_tuple(min_ver):
                reason = f"minimum Sphinx version is {min_ver}"
                marks.append(pytest.mark.skip(reason))
        yield pytest.param(test_name, marks=marks)


@pytest.mark.with_sphinx
@pytest.mark.parametrize('test_name', collect_tests())
def test_sphinx(test_name, app, verify):
    app.build()
    output_dir = OUTPUT_PATH / test_name
    if output_dir.exists():
        shutil.rmtree(output_dir)
    shutil.copytree(app.outdir, output_dir)
    if test_name == 'twotargets':
        verify_output('manual', output_dir, ROOTS_PATH)
        verify_output('reference', output_dir, ROOTS_PATH)
    else:
        verify_output(test_name, output_dir, ROOTS_PATH)
