#!/bin/bash
if [[ ! -d .git ]]; then
    echo "$0 must be run from the project root"
    exit 1
fi
rm -rf dist build soundcraft_utils.egg-info
if [[ $VERSION_SUFFIX ]]; then
    echo "Overriding version with $VERSION_SUFFIX"
    EGG_INFO="egg_info -b $VERSION_SUFFIX"
fi
python3 setup.py $EGG_INFO sdist bdist_wheel || exit 1
[[ -f $BAK ]] && mv $BAK $ORIG
exit 0
