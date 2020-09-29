#
# Copyright (c) 2020 Jim Ramsay <i.am@jimramsay.com>
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

import argparse
import sys

import soundcraft.constants as const

from soundcraft import __version__


def autodetect(dbus=True):
    if dbus:
        try:
            from soundcraft.dbus import Client, DbusInitializationError

            client = Client()
            result = client.autodetect()
            if result is None:
                print("No devices found... waiting for one to appear")
                result = client.waitForDevice()
            return result
        except DbusInitializationError as e:
            print(e)
            sys.exit(2)
    else:
        import soundcraft.notepad

        return soundcraft.notepad.autodetect()


def max_lengths(dev):
    target_len = max([len(x) for x in dev.routingTarget])
    source_len = 0
    for source in dev.sources.values():
        source_len = max(source_len, *[len(x) for x in source])
    for (target, source) in dev.fixedRouting:
        target_len = max(target_len, *[len(x) for x in target])
        source_len = max(source_len, *[len(x) for x in source])
    return (target_len, source_len)


def show(dev):
    (target_len, source_len) = max_lengths(dev)
    table_width = target_len + 4 + source_len + 4
    print("-" * table_width)
    for (target, source) in dev.fixedRouting:
        for i in range(0, len(target)):
            print(f"{target[i]:<{target_len}} <- {source[i]}")
        print("-" * table_width)
    target = [x.ljust(target_len) for x in dev.routingTarget]
    notarget = (" " * target_len, " " * target_len)
    for (i, source) in enumerate(dev.sources.items()):
        sep = "  "
        input = [x.ljust(source_len) for x in source[1]]
        if dev.routingSource is None or dev.routingSource == "UNKNOWN":
            sep = "??"
            selected = target if i == 0 else notarget
        elif dev.routingSource == source[0]:
            selected = target
            sep = "<-"
        else:
            selected = notarget
        for j in range(0, len(selected)):
            idx = f"[{i}]" if j == 0 else ""
            print(f"{selected[j]} {sep} {input[j]} {idx}")
    print("-" * table_width)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s ({const.PACKAGE}) {__version__}",
    )
    parser.add_argument(
        "--no-dbus",
        help="Use direct USB device access instead of D-Bus service access",
        action="store_true",
    )
    parser.add_argument(
        "-l",
        "--list",
        help="List the available source routing options",
        action="store_true",
    )
    parser.add_argument(
        "-s", "--set", help="Set the specified source to route to the USB capture input"
    )
    args = parser.parse_args()
    if args.list or args.set:
        dev = autodetect(dbus=not args.no_dbus)
        if dev is None:
            print("No compatible device detected")
            sys.exit(1)
        print(f"Detected a {dev.name}")
        if args.set:
            try:
                dev.routingSource = args.set
            except ValueError:
                print(f"Unrecognised input choice {args.set}")
                print("Run -l to list the valid choices")
                sys.exit(1)
        show(dev)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
