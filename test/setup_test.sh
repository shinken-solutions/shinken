#!/usr/bin/env bash

set -e

THIS_PATH=$(dirname "$0")
BASE_PATH=$(dirname "$THIS_PATH")

cd $BASE_PATH

# install prog AND tests requirements :
pip install -r shinken/dependencies
pip install -r test/requirements.txt
