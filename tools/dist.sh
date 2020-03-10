#!/bin/bash
if [[ ! -d .git ]]; then
    echo "$0 must be run from the project root"
    exit 1
fi
rm -rf dist build soundcraft_utils.egg-info
if [[ $VERSION_SUFFIX ]]; then
    echo "Overriding version with $VERSION_SUFFIX"
    ORIG=soundcraft/__init__.py
    BAK=${ORIG}.bak
    if [[ -f $BAK ]]; then
        echo "$BAK already exists"
        exit 1
    fi
    sed -i.bak -e "s/^\\(__version__ = ['\"][^'\"]*\\)/\\1$VERSION_SUFFIX/" $ORIG
fi
python3 setup.py sdist bdist_wheel || exit 1
[[ -f $BAK ]] && mv $BAK $ORIG
exit 0
