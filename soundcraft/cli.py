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


def autodetect(dbus=True):
    if dbus:
        try:
            from .dbus import Client, DbusInitializationError

            client = Client()
            result = client.autodetect()
            if result is None:
                print(f"No devices found... waiting for one to appear")
                result = client.waitForDevice()
            return result
        except DbusInitializationError as e:
            print(e)
            sys.exit(2)
    else:
        from .notepad import autodetect as npdetect

        return npdetect()


def show(dev):
    target_length = len(dev.routingTarget)
    source_length = 0
    for (target, source) in dev.fixedRouting.items():
        target_length = max(target_length, len(target))
        source_length = max(source_length, len(source))
    for source in dev.sources.values():
        source_length = max(source_length, len(source))
    table_width = target_length + 4 + source_length + 4
    print("-" * table_width)
    for (target, source) in dev.fixedRouting.items():
        print(f"{target:<{target_length}} <- {source}")
        print("-" * table_width)
    target = dev.routingTarget.ljust(target_length)
    notarget = " " * target_length
    for (i, source) in enumerate(dev.sources.items()):
        sep = "  "
        if dev.routingSource is None or dev.routingSource == "UNKNOWN":
            sep = "??"
            if i == 0:
                selected = target
            else:
                selected = notarget
        elif dev.routingSource == source[0]:
            selected = target
            sep = "<-"
        else:
            selected = notarget
        print(f"{selected} {sep} {source[1]:<{source_length}} [{i}]")
    print("-" * table_width)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--no-dbus",
        help="Use direct USB device access instead of DBUS service access",
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
            print(f"No compatible device detected")
            sys.exit(1)
        print(f"Detected a {dev.name}")
        if args.set:
            try:
                dev.routingSource = args.set
            except ValueError:
                print(f"Unrecognised input choice {args.set}")
                print(f"Run -l to list the valid choices")
                sys.exit(1)
        show(dev)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
