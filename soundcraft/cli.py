import argparse
import sys
from soundcraft.notepad import autodetect

def show(dev):
    print("-"*30)
    for (target, source) in dev.fixedRouting.items():
        print(f"{target} <- {source}")
        print("-"*30)
    first = True
    for source in dev.sources:
        if dev.routingSource is None or dev.routingSource == 'UNKNOWN':
            if first:
                selected = f"{dev.routingTarget} ??"
                first = False
            else:
                selected = f"{' '*12}??"
        elif dev.routingSource == source:
            selected = f"{dev.routingTarget} <-"
        else:
            selected = " "*14
        print(f"{selected} {source}")
    print("-"*30)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-l", "--list", help="List the available source routing options", action="store_true")
    parser.add_argument("-s", "--set", help="Set the specified source to route to the USB capture input")
    args = parser.parse_args()
    if args.list or args.set:
        dev = autodetect()
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

if __name__ == '__main__':
    main()
