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
echo ”----------------------------------------”
ls dist
echo -n "About to release; are you sure? [y/N] "
read answer
if [[ ! $answer =~ ^[yY] ]]; then
    echo "Exiting"
    exit 1
fi
python3 -m twine upload --user __token__ --password $(<$TOOLS/pypi.realkey) dist/*
