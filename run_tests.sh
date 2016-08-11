#!/bin/bash

# usage:
#   run_tests.sh [PYTEST_ARGS]

set -e      # exit as soon as one command returns a non-zero exit code

if [[ $WITH_COVERAGE -eq 1 ]]; then
    COVERAGE_ARGS="--cov=rinoh --cov-report="
else
    COVERAGE_ARGS=
fi

set -x      # echo all lines in the script before executing them

py.test $COVERAGE_ARGS $@
if [[ $WITH_COVERAGE -eq 1 ]]; then
    python coverage.py
fi
