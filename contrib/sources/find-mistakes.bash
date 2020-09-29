#!/bin/bash
#
# Look for some easy to find and easy to miss mistakes in the code.
#
# TODO: Turn this into a pre-commit check?

cd "$(dirname $(dirname $(dirname "$0")))"

find_py_mistake() {
    if git grep "$@" '*.py'
    then
	# Some mistake has been found
	echo "Found mistake(s) for pattern" "$@"
	exit 1
    fi
}

patterns=()
patterns+=('missing_ok')
patterns+=('cached_property')

for mistake_pattern in "${patterns[@]}"
do
    find_py_mistake "$mistake_pattern"
done

exit 0
