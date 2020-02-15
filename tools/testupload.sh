#!/bin/bash
TOOLS=$(dirname $0)
export VERSION_SUFFIX=$1
if [[ ! $VERSION_SUFFIX ]]; then
    echo "usage: $0 [a1|b1|rc1]"
    exit 1
fi
if [[ ! $VERSION_SUFFIX =~ ^(a|b|rc)[0-9]+$ ]]; then
    echo "Suffix must be one of:"
    echo "  a2"
    echo "  b5"
    echo "  rc1"
    exit 2
fi
$TOOLS/dist.sh || exit 1
python3 -m twine upload --user __token__ --password $(<$TOOLS/pypi.testkey) --repository-url https://test.pypi.org/legacy/ dist/*
