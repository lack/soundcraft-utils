import argparse
import sys
from . import autodetect

def show(dev):
    print("-"*30)
    for (usb, channel) in dev.nonmappableChannels.items():
        print(f"capture_{usb} <- {channel}")
        print("-"*30)
    for channel in dev.Channels:
        if dev.selectedChannel() is None:
            if channel == 0:
                selected = f"capture_{dev.mappableChannel} ??"
            else:
                selected = f"{' '*12}??"
        elif dev.selectedChannel() == channel:
            selected = f"capture_{dev.mappableChannel} <-"
        else:
            selected = " "*14
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
