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


def test_format(script_runner):
    do_test_rinoh(script_runner, 'minimal', RINOH_PATH, 'format',
                  ['--format', 'restructuredTEXT'])


def collect_tests():
    for rst_path in sorted(RINOH_PATH.glob('*.rst')):
        yield rst_path.stem


def do_test_rinoh(script_runner, test_name, cwd, output_prefix, extra_args=[]):
    rst_path = RINOH_PATH / Path(test_name + '.rst')
    args = ['--install-resources'] + extra_args
    templconf_path = rst_path.with_suffix('.rtt')
    if templconf_path.exists():
        args += ['--template', str(templconf_path.relative_to(cwd))]
    stylesheet_path = rst_path.with_suffix('.rts')
    if stylesheet_path.exists():
        args += ['--stylesheet', str(stylesheet_path.relative_to(cwd))]
    output_dir = OUTPUT_PATH / f'{output_prefix}_{test_name}'
    output_dir.mkdir(parents=True, exist_ok=True)
    ret = script_runner.run('rinoh', *args, str(rst_path.relative_to(cwd)),
                            '--output', str(output_dir), cwd=str(cwd))
    assert ret.success
    verify_output(test_name, output_dir, RINOH_PATH)


@pytest.mark.parametrize('test_name', collect_tests())
def test_rinoh_in_cwd(script_runner, test_name):
    do_test_rinoh(script_runner, test_name, RINOH_PATH, "in_cwd")


@pytest.mark.parametrize('test_name', collect_tests())
def test_rinoh_relative_to_cwd(script_runner, test_name):
    do_test_rinoh(script_runner, test_name, Path.cwd(), "relative_to_cwd")


def test_rinoh_stylesheet_not_found(script_runner):
    args = ['--stylesheet', 'missing.rts']
    ret = script_runner.run('rinoh', *args, str(RINOH_PATH / 'minimal.rst'))
    assert not ret.success
    assert "Could not find the style sheet" in ret.stderr
