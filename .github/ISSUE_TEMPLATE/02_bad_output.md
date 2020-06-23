---
name: Bad output report
about: rinohtype produces a PDF with wrong layout or other issues 
title: ''
labels: bug, bad output
assignees: ''

---

Sometimes bugs have already been fixed in the master branch. Please try to
reproduce the issue with the current master version of rinohtype before you
file a bug report. You can install it directly from GitHub like this:

    pip install git+https://github.com/brechtm/rinohtype.git@master

Please provide the following information to make your bug report as useful as
possible.

1. Include the **produced PDF** and describe what you think is wrong.
2. A link to the **source files** (e.g. Sphinx project). Without this, it would
   take too much time to reproduce the bug. If you cannot share the source
   files publicly, try to create dummy input files that reproduce the bug (may
   be difficult). Alternatively, you can send the input files to us privately.
   Look for an email address in the main
   [readme](https://github.com/brechtm/rinohtype#rinohtype).

Please also provide the following information:
* rinohtype version: (output from `rinoh --version`)
* Sphinx version: (output from `sphinx-build --version`)
* Python version: (output from `python --version`)
* operating system: (Windows, Linux, MacOS)
