#!/bin/sh

cd "$(dirname $(dirname $(dirname "$0")))"

# Using [] character class to prevent this line from finding itself.
git grep -i -E '([f]ixme|[t]odo)'
