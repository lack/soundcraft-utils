#!/bin/bash
TOOLS=$(dirname $0)
grep version soundcraft/__init__.py
echo -n "About to release; are you sure? [y/N] "
read answer
if [[ ! $answer =~ ^[yY] ]]; then
    echo "Exiting"
    exit 1
fi
$TOOLS/dist.sh || exit 1
python3 -m twine upload --user __token__ --password $(<$TOOLS/pypi.realkey) dist/*
