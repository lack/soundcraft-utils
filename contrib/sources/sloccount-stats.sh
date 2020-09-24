#!/bin/sh

cd "$(dirname $(dirname $(dirname "$0")))"

sloccount soundcraft contrib test tools
