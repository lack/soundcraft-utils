#
# Copyright (c) 2020 Jim Ramsay <i.am@jimramsay.com>
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


import argparse
import shutil
import subprocess
import sys
from pathlib import Path
from string import Template


import soundcraft

import soundcraft.constants as const
from soundcraft.dbus import BUSNAME, Client


def findDataFiles(subdir):
    """Walk through data files in the soundcraft module's ``data`` subdir``"""

    result = {}
    modulepaths = soundcraft.__path__
    for path in modulepaths:
        path = Path(path)
        datapath = path / "data" / subdir
        result[datapath] = []
        for f in datapath.glob("**/*"):
            if f.is_dir():
                continue
            result[datapath].append(f.relative_to(datapath))
    return result


def serviceExePath():
    exename = Path(sys.argv[0]).resolve()
    if exename.suffix == ".py":
        raise ValueError(
            "Running setup out of a module-based execution is not supported"
        )
    return exename


SCALABLE_ICONDIR = Path("/usr/local/share/icons/hicolor/scalable/apps/")


def setup_dbus(cfgroot=Path("/usr/share/dbus-1")):
    templateData = {
        "dbus_service_bin": str(serviceExePath()),
        "busname": BUSNAME,
    }
    sources = findDataFiles("dbus-1")
    for (srcpath, files) in sources.items():
        for f in files:
            src = srcpath / f
            dst = cfgroot / f
            print(f"Installing {src} -> {dst}")
            with open(src, "r") as srcfile:
                srcTemplate = Template(srcfile.read())
                with open(dst, "w") as dstfile:
                    dstfile.write(srcTemplate.substitute(templateData))
    print(f"Starting service version {soundcraft.__version__}...")
    client = Client()
    print(f"Version running: {client.serviceVersion()}")
    print("D-Bus setup is complete")
    print(f"Run {const.BASE_EXE_GUI} or {const.BASE_EXE_CLI} as a regular user")


def setup_xdg():
    sources = findDataFiles("xdg")
    for (srcpath, files) in sources.items():
        for f in files:
            src = srcpath / f
            if src.suffix == ".desktop":
                subprocess.run(["xdg-desktop-menu", "install", "--novendor", str(src)])
            elif src.suffix == ".png":
                for size in (16, 24, 32, 48, 256):
                    subprocess.run(
                        [
                            "xdg-icon-resource",
                            "install",
                            "--novendor",
                            "--size",
                            str(size),
                            str(src),
                        ]
                    )
            elif src.suffix == ".svg":
                SCALABLE_ICONDIR.mkdir(parents=True, exist_ok=True)
                shutil.copy(src, SCALABLE_ICONDIR)
    print("Installed all XDG application launcher files")


def setup():
    setup_dbus()
    setup_xdg()


def uninstall_dbus(cfgroot=Path("/usr/share/dbus-1")):
    try:
        client = Client()
        print(f"Shutting down service version {client.serviceVersion()}")
        client.shutdown()
        print("Stopped")
    except Exception:
        print("Service not running")
    sources = findDataFiles("dbus-1")
    for (srcpath, files) in sources.items():
        for f in files:
            path = cfgroot / f
            print(f"Removing {path}")
            try:
                path.unlink()
            except Exception as e:
                print(e)
    print("D-Bus service is unregistered")


def uninstall_xdg():
    sources = findDataFiles("xdg")
    for (srcpath, files) in sources.items():
        for f in files:
            print(f"Uninstalling {f.name}")
            if f.suffix == ".desktop":
                subprocess.run(["xdg-desktop-menu", "uninstall", "--novendor", f.name])
            elif f.suffix == ".png":
                for size in (16, 24, 32, 48, 256):
                    subprocess.run(
                        ["xdg-icon-resource", "uninstall", "--size", str(size), f.name]
                    )
            elif f.suffix == ".svg":
                svg = SCALABLE_ICONDIR / f.name
                try:
                    svg.unlink()
                except FileNotFoundError:
                    pass  # svg file not found
    print("Removed all XDG application launcher files")


def uninstall():
    uninstall_dbus()
    uninstall_xdg()


def main():
    parser = argparse.ArgumentParser(
        description=f"Set up/clean up {const.PACKAGE} (install/uninstall)."
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s ({const.PACKAGE}) {soundcraft.__version__}",
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--install",
        help=f"Install and set up {const.PACKAGE} and exit",
        action="store_true",
    )
    group.add_argument(
        "--uninstall",
        help="Undo any installation and setup performed by --install and exit",
        action="store_true",
    )

    args = parser.parse_args()
    if args.install:
        setup()
    elif args.uninstall:
        uninstall()
