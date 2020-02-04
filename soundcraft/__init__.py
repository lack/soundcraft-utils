import argparse
import sys
from .notepad import *

__version__ = "0.1.2"

def autodetect():
    for devType in ('12fx', '8fx', '5'):
        dev = eval(f"Notepad_{devType}()");
        if dev is not None:
            return dev

def show(dev):
    print("-"*30)
    for (usb, channel) in dev.nonmappableChannels.items():
        print(f"capture_{usb} <- {channel}")
        print("-"*30)
    for channel in dev.Channels:
        selected = f"capture_{dev.mappableChannel} <-" if dev.selectedChannel() == channel else " "*14
        print(f"{selected} {channel.name: <10} ({channel})")
    print("-"*30)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-l", "--list", help="List the available channel selection options", action="store_true")
    parser.add_argument("-s", "--set", help="Set the USB input mappi g to the specified input")
    args = parser.parse_args()
    if args.list: 
        dev = autodetect()
        print(f"Detected a {dev.name()}")
        show(dev)
    elif args.set:
        dev = autodetect()
        print(f"Detected a {dev.name()}")
        channel = dev.parseChannel(args.set)
        if channel is None:
            print(f"Unrecognised input choice {args.set}")
            print(f"Run -l to list the valid choices")
            sys.exit(1)
        dev.switchChannel(channel)
        show(dev)
    else:
        parser.print_help()
