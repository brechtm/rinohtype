# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.

import pytest

import shutil

from pathlib import Path

from helpers.regression import verify_output


TESTS_PATH = Path(__file__).parent
ROOTS_PATH = TESTS_PATH / 'sphinx'
OUTPUT_PATH = TESTS_PATH / 'sphinx_output'
OUTPUT_PATH.mkdir(exist_ok=True)


def collect_tests():
    for root_path in sorted(ROOTS_PATH.glob('test-*')):
        test_name = root_path.stem.replace('test-', '')
        yield pytest.param(test_name,
                           marks=pytest.mark.sphinx(buildername='rinoh',
                                                    testroot=test_name))


@pytest.mark.parametrize('test_name', collect_tests())
def test_sphinx(test_name, app, verify):
    app.build()
    output_dir = OUTPUT_PATH / test_name
    if output_dir.exists():
        shutil.rmtree(output_dir)
    shutil.copytree(app.outdir, output_dir)
    verify_output(test_name, output_dir, ROOTS_PATH)
