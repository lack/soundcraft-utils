#!/bin/sh

cd "$(dirname $(dirname $(dirname "$0")))"

git log | grep ^Author: \
    | sed 's|^Author: lack <i.am@jimramsay.com>$|Author: Jim Ramsay <i.am@jimramsay.com>|' \
    | sort | uniq -c | sort -bgr
