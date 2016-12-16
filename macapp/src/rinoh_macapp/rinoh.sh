#!/bin/bash

# Wrapper script that runs rinoh using the Python interpreter embedded in the
# application bundle and passes on command line arguments

SCRIPT_DIR="$(dirname "$(readlink "$0")")"
CONTENTS_DIR=$( cd "$SCRIPT_DIR/../../.." && pwd )
export PYTHONPATH="$CONTENTS_DIR/Resources/app_packages"
PYTHON="$CONTENTS_DIR/Resources/python/bin/python3"

$PYTHON -m rinoh.tool "$@"
