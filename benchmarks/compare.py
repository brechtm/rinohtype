# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


"""Compare font-loading and rendering speed against another git revision

Seven measurements are run, each in a process of its own:

``fonts``
    Load every font file shipped by the installed ``rinoh-typeface-*``
    packages and use each one the way a rendering pass does: glyph metrics
    for the characters of a sample text and the kerning of its character
    pairs.

``render``
    A single rendering pass of ``benchmarks/refmanual.py`` (see there),
    excluding parsing the input document.

``steps``
    The number of Python bytecode instructions executed by that same
    rendering pass, counted with ``sys.monitoring`` (Python 3.12 or newer).
    This is a portable, deterministic stand-in for cachegrind's instruction
    count on platforms where Valgrind is unavailable; unlike the timings, it
    is reported as a count rather than a duration.

``manual`` and ``reference``
    A single rendering pass of the rinohtype user manual and reference
    guide (``doc/manual.rst`` and ``doc/reference.rst``, as built by the
    Sphinx builder), excluding the Sphinx build and the conversion to the
    rinohtype document tree.

``manual-steps`` and ``reference-steps``
    The number of Python bytecode instructions executed by those rendering
    passes. Counting instructions with ``sys.monitoring`` slows rendering
    down considerably, so these are measured once per side instead of
    ``--repeat`` times. They are deterministic, like ``steps``.

With ``--baseline``, all measurements also run against the source tree of
that git revision, checked out in a temporary worktree. The runs alternate,
so a change in clock speed or system load affects both sides equally.

    python benchmarks/compare.py                    # the current tree only
    python benchmarks/compare.py --baseline HEAD~1
    python benchmarks/compare.py --baseline v0.5.0 --repeat 7

The measured time is CPU time (``time.process_time()``); compare the medians.
``--verbose`` prints every sample.
"""


import argparse
import glob
import os
import shutil
import statistics
import subprocess
import sys
import sysconfig
import tempfile
import time
import warnings

from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parent
SRC_PATH = REPO / 'src'

#: the Sphinx documents to render, by `rinoh_documents` target
DOCUMENTS = ('manual', 'reference')

#: bytecode instruction counts are deterministic; these are counted once
DOCUMENT_STEPS = tuple(document + '-steps' for document in DOCUMENTS)

#: the measurements, in reporting order
MEASUREMENTS = (('fonts', 'render', 'steps')
                + tuple(kind for document in DOCUMENTS
                        for kind in (document, document + '-steps')))

SAMPLE_TEXT = ('The quick brown fox jumps over the lazy dog. '
               'AVATAR Wonderful Typography, 0123456789!?\u00e9')
KERNING_PAIRS = list(zip(SAMPLE_TEXT, SAMPLE_TEXT[1:]))

#: for a deterministic, single-pass rendering measurement
DETERMINISTIC_ENV = dict(RINOH_SINGLE_PASS='1', RINOH_NO_CACHE='1',
                         PYTHONHASHSEED='0')


# the measurements, run in a worker process

def font_files():
    """The font files shipped by the installed rinoh-typeface-* packages"""
    pattern = os.path.join(sysconfig.get_paths()['purelib'],
                           'rinoh_typeface_*', '*.[ot]tf')
    files = sorted(glob.glob(pattern))
    if not files:
        raise SystemExit('No rinoh-typeface-* font files are installed')
    return files


def measure_fonts(font_class):
    """Load and use every font, the way rendering a document does"""
    warnings.simplefilter('ignore')     # the sample text may miss a glyph
    for filename in font_files():
        font = font_class(filename)
        for char in set(SAMPLE_TEXT):
            font.get_glyph_metrics(char, 'normal')
        for a, b in KERNING_PAIRS:
            font.get_kerning(font.get_glyph_metrics(a, 'normal'),
                             font.get_glyph_metrics(b, 'normal'))


def fonts_worker():
    from rinoh.font.opentype import OpenTypeFont      # not measured
    cpu = time.process_time()
    measure_fonts(OpenTypeFont)
    print(time.process_time() - cpu)


def steps_worker(out_dir):
    sys.path.insert(0, str(HERE))
    import refmanual
    document = refmanual.prepare_document()     # not measured
    refmanual.measure_under_bytecode_steps(
        lambda: refmanual.render(document, Path(out_dir)))


def render_worker(out_dir):
    sys.path.insert(0, str(HERE))
    import refmanual
    document = refmanual.prepare_document()     # not measured
    cpu = time.process_time()
    refmanual.render(document, Path(out_dir))
    print(time.process_time() - cpu)


def document_worker(target, src_path, out_dir, doctree_dir, steps=False):
    """Render a document built by the Sphinx builder, such as the manual"""
    from copy import copy

    from sphinx.application import Sphinx
    from sphinx.util import logging

    logger = logging.getLogger(__name__)
    doc_path = Path(src_path).parent / 'doc'
    devnull = open(os.devnull, 'w')
    app = Sphinx(str(doc_path), str(doc_path), str(out_dir),
                 str(doctree_dir), 'rinoh', freshenv=False,
                 warningiserror=False, verbosity=0,
                 status=devnull, warning=devnull)
    builder = app.builder
    builder.read()                              # not measured
    document_data = {entry['target']: entry
                     for entry in builder.document_data(logger)}
    document = builder.construct_rinohtype_document(
        copy(document_data[target]))
    def render_document():
        stdout, sys.stdout = sys.stdout, devnull    # the progress indicator
        try:
            document.render(Path(out_dir) / target)
        finally:
            sys.stdout = stdout

    if steps:
        sys.path.insert(0, str(HERE))
        import refmanual
        # prints the number of instructions executed
        return refmanual.measure_under_bytecode_steps(render_document)
    cpu = time.process_time()
    render_document()
    print(time.process_time() - cpu)


# driving the workers, in the parent process

def worker_env(src_path):
    python_path = os.environ.get('PYTHONPATH')
    paths = [str(src_path)] + ([python_path] if python_path else [])
    return dict(os.environ, PYTHONPATH=os.pathsep.join(paths),
                **DETERMINISTIC_ENV)


def run_worker(kind, src_path, out_dir, side):
    command = [sys.executable, __file__, '--worker', kind]
    if kind in ('render', 'steps'):
        command += ['--out-dir', str(out_dir)]
    elif kind in DOCUMENTS or kind in DOCUMENT_STEPS:
        command += ['--out-dir', str(out_dir),
                    '--doctree-dir', str(out_dir / ('doctrees-' + side))]
    result = subprocess.run(command, capture_output=True, text=True,
                            env=worker_env(src_path))
    if result.returncode:
        raise SystemExit('The {} measurement failed:\n{}'
                         .format(kind, result.stderr.strip()))
    return float(result.stdout.split()[-1])


def add_worktree(revision, path):
    """Check out `revision` in a new worktree and return its source path"""
    result = subprocess.run(['git', '-C', str(REPO), 'worktree', 'add',
                             '--detach', str(path), revision],
                            capture_output=True, text=True)
    if result.returncode:
        raise SystemExit('Cannot check out {}:\n{}'
                         .format(revision, result.stderr.strip()))
    if not (path / 'src' / 'rinoh').is_dir():
        raise SystemExit('{} does not contain a src/rinoh directory'
                         .format(revision))
    return path / 'src'


def remove_worktree(path):
    subprocess.run(['git', '-C', str(REPO), 'worktree', 'remove', '--force',
                    str(path)], capture_output=True)


def summarise(kind, samples):
    if kind == 'steps' or kind in DOCUMENT_STEPS:
        values = [int(sample) for sample in samples]
        return 'median {:,} steps (min {:,}, max {:,})'.format(
            int(statistics.median(values)), min(values), max(values))
    return 'median {:.3f} s (min {:.3f} s, max {:.3f} s)'.format(
        statistics.median(samples), min(samples), max(samples))


def sample_line(kind, side, value):
    if kind == 'steps' or kind in DOCUMENT_STEPS:
        return '{:<15s} {:8s} {:,} steps'.format(kind, side, int(value))
    return '{:<15s} {:8s} {:.4f} s'.format(kind, side, value)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--baseline', metavar='REV',
                        help='git revision to compare against')
    parser.add_argument('--repeat', type=int, default=5, metavar='N',
                        help='number of runs per measurement and side '
                             '(default: %(default)s)')
    parser.add_argument('--warmup', type=int, default=1, metavar='N',
                        help='number of discarded runs per measurement and '
                             'side (default: %(default)s)')
    parser.add_argument('--verbose', action='store_true',
                        help='print every sample')
    parser.add_argument('--worker',
                        choices=('fonts', 'render', 'steps')
                        + DOCUMENTS + DOCUMENT_STEPS,
                        help=argparse.SUPPRESS)
    parser.add_argument('--out-dir', type=Path, help=argparse.SUPPRESS)
    parser.add_argument('--doctree-dir', type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()

    if args.worker == 'fonts':
        return fonts_worker()
    if args.worker == 'render':
        return render_worker(args.out_dir)
    if args.worker == 'steps':
        return steps_worker(args.out_dir)
    if args.worker in DOCUMENTS or args.worker in DOCUMENT_STEPS:
        document_worker(args.worker.split('-')[0], SRC_PATH, args.out_dir,
                        args.doctree_dir, steps=args.worker in DOCUMENT_STEPS)
        return

    if args.baseline and not (REPO / '.git').exists():
        raise SystemExit('--baseline needs a git checkout in {}'.format(REPO))

    worktree = None
    temp_dir = Path(tempfile.mkdtemp(prefix='rinoh-benchmark-'))
    try:
        baseline_src = None
        if args.baseline:
            worktree = temp_dir / 'baseline'
            baseline_src = add_worktree(args.baseline, worktree)
        samples = {}
        for kind in MEASUREMENTS:
            out_dir = temp_dir / kind
            out_dir.mkdir()
            current, baseline = [], []
            single_run = kind in DOCUMENT_STEPS
            repetitions = 1 if single_run else args.warmup + args.repeat
            for repetition in range(repetitions):
                current.append(run_worker(kind, SRC_PATH, out_dir, 'current'))
                if baseline_src:
                    baseline.append(run_worker(kind, baseline_src, out_dir,
                                               'baseline'))
            if not single_run:
                current, baseline = current[args.warmup:], \
                    baseline[args.warmup:]
            if args.verbose:
                for value in current:
                    print(sample_line(kind, 'current', value))
                for value in baseline:
                    print(sample_line(kind, 'baseline', value))
            samples[kind] = (current, baseline)
    finally:
        if worktree:
            remove_worktree(worktree)
        shutil.rmtree(temp_dir, ignore_errors=True)

    print()
    for kind, (current, baseline) in samples.items():
        line = '{:<15s} current {}'.format(kind, summarise(kind, current))
        if baseline:
            ratio = statistics.median(current) / statistics.median(baseline)
            line += '   baseline {}   {:+.1f} %'.format(
                summarise(kind, baseline), (ratio - 1) * 100)
        print(line)
    if args.baseline:
        print('\nbaseline: {}'.format(args.baseline))


if __name__ == '__main__':
    main()
