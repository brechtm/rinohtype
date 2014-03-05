#!/bin/sh

THISDIR="$(dirname $0)"
ROOTDIR="$THISDIR/../.."

export PYTHONPATH=$ROOTDIR:$PYTHONPATH

env python3 test.py

