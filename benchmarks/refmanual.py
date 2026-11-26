# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.

"""Deterministic rendering benchmark

Renders refmanual.rst, the reference manual of a fictional Python library
(random filler text) that exercises the typical mix of elements found in
technical documentation: a table of contents, chapters starting on a new page,
tables spanning pages, syntax-highlighted code blocks, nested lists, figures
and cross-references.

Only rinohtype's rendering is measured: a single rendering pass, writing the
style log and the PDF file (RINOH_SINGLE_PASS, RINOH_NO_CACHE). Parsing the
reStructuredText input happens before that.

``python benchmarks/refmanual.py``
    Render natively and report the wall-clock and CPU time.

``python benchmarks/refmanual.py --instructions``
    Re-run this script under Valgrind's cachegrind and report the number of
    CPU instructions executed while rendering. Re-run it once more to report
    the peak memory allocated while rendering, traced by tracemalloc (memory
    allocated by Python, not by extension modules). These numbers do not
    depend on the CPU's speed, its clock frequency or the system load;
    repeated runs agree to within a few hundred instructions (out of
    billions). They do depend on the Python interpreter, the versions of the
    dependencies and, slightly, on the path of the rinohtype checkout, so
    only compare numbers obtained in the same environment. ``--profile
    FILE`` keeps cachegrind's per-function counts (``cg_annotate FILE``).

Cachegrind starts with instrumentation disabled (--instr-at-start=no), so
startup, imports and parsing run at near-native speed. The script switches
instrumentation on and off around render() with Valgrind client requests,
issued through a few bytes of machine code called via ctypes (x86-64 only).
"""

import argparse
import ctypes
import mmap
import os
import platform
import subprocess
import sys
import tempfile
import time
import tracemalloc

from pathlib import Path


HERE = Path(__file__).resolve().parent


def prepare_document():
    """Return a Document ready for rendering (not part of the measurement)"""
    from rinoh.frontend.rst import ReStructuredTextReader
    from rinoh.template import TemplateConfigurationFile

    doctree = ReStructuredTextReader().parse(HERE / 'refmanual.rst')
    configuration = TemplateConfigurationFile(HERE / 'refmanual.rtt')
    return configuration.document(doctree)


def render(document, out_dir):
    with open(os.devnull, 'w') as devnull:      # the progress indicator
        stdout, sys.stdout = sys.stdout, devnull
        try:
            document.render(Path(out_dir) / 'refmanual')
        finally:
            sys.stdout = stdout
# Valgrind client requests are special no-op instruction sequences that
# Valgrind recognizes. This function (x86-64, System V calling convention)
# performs the request described by the array of 6 words its argument points
# to (request code and 5 arguments) and returns the result (0 when not running
# under Valgrind). See valgrind.h.
CLIENT_REQUEST_X86_64 = bytes([
    0x48, 0x89, 0xf8,           # mov    %rdi,%rax   (address of the array)
    0x31, 0xd2,                 # xor    %edx,%edx   (default result)
    0x48, 0xc1, 0xc7, 0x03,     # rol    $3,%rdi     (the special sequence)
    0x48, 0xc1, 0xc7, 0x0d,     # rol    $13,%rdi
    0x48, 0xc1, 0xc7, 0x3d,     # rol    $61,%rdi
    0x48, 0xc1, 0xc7, 0x33,     # rol    $51,%rdi
    0x48, 0x87, 0xdb,           # xchg   %rbx,%rbx
    0x48, 0x89, 0xd0,           # mov    %rdx,%rax   (result)
    0xc3])                      # ret

CG_START_INSTRUMENTATION = ord('C') << 24 | ord('G') << 16    # cachegrind.h
CG_STOP_INSTRUMENTATION = CG_START_INSTRUMENTATION + 1


def client_request_function():
    if platform.machine() not in ('x86_64', 'AMD64'):
        raise SystemExit('Counting instructions is only supported on x86-64')
    memory = mmap.mmap(-1, mmap.PAGESIZE,
                       prot=mmap.PROT_READ | mmap.PROT_WRITE | mmap.PROT_EXEC)
    memory.write(CLIENT_REQUEST_X86_64)
    address = ctypes.addressof(ctypes.c_char.from_buffer(memory))
    function = ctypes.CFUNCTYPE(ctypes.c_size_t,
                                ctypes.POINTER(ctypes.c_size_t))(address)

    def client_request(request):
        arguments = (ctypes.c_size_t * 6)(request, 0, 0, 0, 0, 0)
        return function(arguments)

    client_request.memory = memory      # keep the code alive
    return client_request


def measure_native(document, out_dir):
    wall, cpu = time.perf_counter(), time.process_time()
    render(document, out_dir)
    wall, cpu = time.perf_counter() - wall, time.process_time() - cpu
    print('render: {:.2f} s wall, {:.2f} s CPU'.format(wall, cpu))


def measure_under_cachegrind(document, out_dir):
    client_request = client_request_function()
    client_request(CG_START_INSTRUMENTATION)
    render(document, out_dir)
    client_request(CG_STOP_INSTRUMENTATION)


def measure_under_tracemalloc(document, out_dir):
    tracemalloc.start()
    render(document, out_dir)
    print(tracemalloc.get_traced_memory()[1])     # the peak


def count_instructions(args, out_dir):
    """Run this script under cachegrind and return the instruction count"""
    output = Path(args.profile or Path(out_dir) / 'cachegrind.out')
    command = ['valgrind', '--tool=cachegrind', '--cache-sim=no',
               '--instr-at-start=no',
               '--cachegrind-out-file={}'.format(output),
               sys.executable, __file__, '--under-cachegrind',
               '--out-dir', str(out_dir)]
    result = subprocess.run(command, env=environment(),
                            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
                            text=True)
    if result.returncode:
        raise SystemExit(result.stderr)
    with output.open() as file:
        summary, = (line for line in file if line.startswith('summary:'))
    return int(summary.split()[1])


def peak_memory(out_dir):
    """Run this script with tracemalloc and return the peak memory usage"""
    command = [sys.executable, __file__, '--under-tracemalloc',
               '--out-dir', str(out_dir)]
    result = subprocess.run(command, env=environment(), capture_output=True,
                            text=True)
    if result.returncode:
        raise SystemExit(result.stderr)
    return int(result.stdout.split()[-1])


def environment():
    """Environment variables for a deterministic, single-pass render"""
    return dict(os.environ, RINOH_SINGLE_PASS='1', RINOH_NO_CACHE='1',
                PYTHONHASHSEED='0')


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--instructions', action='store_true',
                        help='count instructions using Valgrind (cachegrind) '
                             'and trace the peak memory usage')
    parser.add_argument('--profile', metavar='FILE', type=Path,
                        help='keep the cachegrind output file, a per-function '
                             'profile (implies --instructions)')
    parser.add_argument('--out-dir', type=Path,
                        help='directory for the output files (default: a '
                             'temporary directory)')
    parser.add_argument('--under-cachegrind', action='store_true',
                        help=argparse.SUPPRESS)
    parser.add_argument('--under-tracemalloc', action='store_true',
                        help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.under_cachegrind:
        document = prepare_document()
        return measure_under_cachegrind(document, args.out_dir)
    if args.under_tracemalloc:
        document = prepare_document()
        return measure_under_tracemalloc(document, args.out_dir)
    if not (args.instructions or args.profile) \
            and os.environ.get('PYTHONHASHSEED') != '0':
        # render under the same conditions as with --instructions
        os.execve(sys.executable, [sys.executable] + sys.argv, environment())
    with tempfile.TemporaryDirectory() as temp_dir:
        out_dir = (args.out_dir or Path(temp_dir)).resolve()
        out_dir.mkdir(parents=True, exist_ok=True)
        if args.instructions or args.profile:
            if args.profile:
                args.profile = args.profile.resolve()
            instructions = count_instructions(args, out_dir)
            print('render: {:,} instructions'.format(instructions))
            print('render: {:.2f} MB peak memory'
                  .format(peak_memory(out_dir) / 1e6))
            if args.profile:
                print('profile: cg_annotate {}'.format(args.profile))
        else:
            measure_native(prepare_document(), out_dir)


if __name__ == '__main__':
    main()
