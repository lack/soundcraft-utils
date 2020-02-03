import argparse
import sys
from .notepad import *

__version__ = "0.1.0"

def autodetect():
    for devType in ('12fx', '8fx', '5'):
        dev = eval(f"Notepad_{devType}()");
        if dev is not None:
            return dev

def show(dev):
    print(f"Detected a {dev.name()}")
    print("Available channels:")
    for channel in dev.Channels:
        print(f"  {channel} => {channel.name}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-l", "--list", help="List the available channel selection options", action="store_true")
    parser.add_argument("-s", "--set", help="Set the USB input mappi g to the specified input")
    args = parser.parse_args()
    if args.list: 
        dev = autodetect()
        show(dev)
    elif args.set:
        dev = autodetect()
        channel = dev.parseChannel(args.set)
        if channel is None:
            print(f"Unrecognised input choice {args.set}")
            print(f"Run -l to list the valid choices")
            sys.exit(1)
        print(f"Would set to {channel} ({channel.name})")
        dev.switchChannel(channel)
    else:
        parser.print_help()
