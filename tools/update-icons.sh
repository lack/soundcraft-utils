#!/bin/sh
# Update scaled *.png icon files from the original *.svg file
#
########################################################################
# Copyright (c) 2020 Hans Ulrich Niedermann <hun@n-dimensional.de>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
########################################################################
#
# Update the scaled *.png versions of the icon from the source svg
# file.  This requires inkscape, so the results are intended to be
# committed to the git source tree, so that normal build systems do
# not require inkscape.
#
# There is no guarantee that the generated files are bit by bit
# identical when this script runs different versions of inkscape and
# the libraries it depends on.

set -e

# Allow the user to set INKSCAPE to whatever path and command they need.
if test "x$INKSCAPE" = "x"
then
    INKSCAPE=inkscape
fi

# Make sure the given inkscape is present and can be run
${INKSCAPE} --version

# Change to top source directory
cd "$(dirname $(dirname "$0"))"

# File locations
icon_dir="soundcraft/data/xdg"

# Avoid hard coding the actual icon name by using a wildcard...
for svgicon in ${icon_dir}/*.svg
do
    # ...while not finding any svg icon at all is an error.
    test -f "$svgicon"

    iconbase="$(basename "$svgicon" .svg)"

    for size in 16 24 32 48 64 96 128 192 256
    do
	destpng="${icon_dir}/${iconbase}.${size}.png"
	if test -f "$destpng" && test "$destpng" -nt "$svgicon"; then
	    echo "$destpng already up to date"
	else
	    echo "$destpng to be updated"
	    ${INKSCAPE} -o "$destpng" --export-area-page -w "$size" -h "$size" "$svgicon"
	fi
    done
done
