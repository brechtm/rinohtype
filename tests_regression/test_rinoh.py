# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.

from pathlib import Path

import pytest

from helpers.regression import verify_output


RINOH_PATH = Path(__file__).parent / 'rinoh'
OUTPUT_PATH = Path(__file__).parent / 'rinoh_output'


def test_version(script_runner):
    ret = script_runner.run('rinoh', '--version')
    assert ret.success
    assert ret.stderr == ''


def test_list_formats(script_runner):
    ret = script_runner.run('rinoh', '--list-formats')
    assert ret.success
    assert ret.stderr == ''
    assert '[built-in]' in ret.stdout
    assert 'CommonMark' in ret.stdout
    assert 'reStructuredText' in ret.stdout


def collect_tests():
    for rst_path in sorted(RINOH_PATH.glob('*.rst')):
        yield (pytest.param(rst_path.stem, marks=pytest.mark.xfail)
               if rst_path.stem == 'install_resources' else rst_path.stem)


@pytest.mark.parametrize('test_name', collect_tests())
def test_rinoh(script_runner, test_name):
    rst_path = Path(test_name + '.rst')
    args = ['--install-resources']
    templconf_path = rst_path.with_suffix('.rtt')
    if (RINOH_PATH / templconf_path).exists():
        args += ['--template', str(templconf_path)]
    stylesheet_path = rst_path.with_suffix('.rts')
    if (RINOH_PATH / stylesheet_path).exists():
        args += ['--stylesheet', str(stylesheet_path)]
    output_dir = OUTPUT_PATH / ('rinoh_' + test_name)
    output_dir.mkdir(parents=True, exist_ok=True)
    ret = script_runner.run('rinoh', *args, str(rst_path),
                            '--output', str(output_dir), cwd=RINOH_PATH)
    assert ret.success
    verify_output(test_name, output_dir, RINOH_PATH)
