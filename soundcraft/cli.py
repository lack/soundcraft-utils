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
    print("-" * 30)
    for (target, source) in dev.fixedRouting.items():
        print(f"{target} <- {source}")
        print("-" * 30)
    for (i, source) in enumerate(dev.sources):
        if dev.routingSource is None or dev.routingSource == "UNKNOWN":
            if i == 0:
                selected = f"{dev.routingTarget} ??"
            else:
                selected = f"{' '*12}??"
        elif dev.routingSource == source:
            selected = f"{dev.routingTarget} <-"
        else:
            selected = " " * 14
        print(f"{selected} {source:<10} [{i}]")
    print("-" * 30)


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
