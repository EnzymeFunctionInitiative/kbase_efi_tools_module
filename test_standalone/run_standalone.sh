#!/bin/bash

bindir=$(cd $(dirname $0) && pwd)
#libdir="$bindir/../lib"
export PYTHONPATH=$PYTHONPATH:"/kb/module/lib"
echo "PYTHONPATH=$PYTHONPATH"

echo "RUNNING $bindir/est_test.py"
pytest "$bindir/est_test.py"

