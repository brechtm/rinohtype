#!/bin/sh

THISDIR="$(dirname $0)"
ROOTDIR="$THISDIR/../.."

export PYTHONPATH=$ROOTDIR:$ROOTDIR/citeproc-py:$PYTHONPATH

env python3 template.py

