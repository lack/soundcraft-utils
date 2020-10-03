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
import time
from pathlib import Path
from string import Template


try:
    import gi  # noqa: F401 'gi' imported but unused
except ModuleNotFoundError:
    print(
        """
The PyGI library must be installed from your distribution; usually called
python-gi, python-gobject, python3-gobject, pygobject, or something similar.
"""
    )
    raise

# We only need the whole gobject and GLib thing here to catch specific exceptions
from gi.repository.GLib import Error as GLibError


import pydbus

import soundcraft

import soundcraft.constants as const
from soundcraft.dbus import BUSNAME


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


def find_datadir():
    exe_path = serviceExePath()
    for prefix in [Path("/usr/local"), Path("/usr"), Path("~/.local").expanduser()]:
        for sx_dir in ["bin", "sbin", "libexec"]:
            for sx in [const.BASE_EXE_SETUP]:
                sx_path = prefix / sx_dir / sx
                if sx_path == exe_path:
                    return prefix / "share"
                try:
                    exe_path.relative_to(prefix)  # ignore result

                    # If this is
                    # ``/home/user/.local/share/virtualenvs/soundcraft-utils-ABCDEFG/bin/soundcraft_setup``,
                    # then the D-Bus and XDG config can either go into
                    # ``/home/user/.local/share/virtualenvs/soundcraft-utils-ABCDEFG/share/``
                    # and be ignored, or go into
                    # ``/home/user/.local/share/`` and work. We choose
                    # the latter.
                    return prefix / "share"
                except ValueError:
                    pass  # exe_path is not a subdir of prefix
    raise ValueError(f"Service exe path is not supported: {exe_path!r}")


def install_dbus():
    dbus1_root = find_datadir() / "dbus-1"
    print(f"Using dbus-1 config root {dbus1_root}")
    templateData = {
        "dbus_service_bin": str(serviceExePath()),
        "busname": BUSNAME,
    }
    sources = findDataFiles("dbus-1")
    for (srcpath, files) in sources.items():
        for f in files:
            src = srcpath / f
            dst = dbus1_root / f
            print(f"Installing {src} -> {dst}")
            with open(src, "r") as srcfile:
                srcTemplate = Template(srcfile.read())
                with open(dst, "w") as dstfile:
                    dstfile.write(srcTemplate.substitute(templateData))

    bus = pydbus.SystemBus()
    dbus_service = bus.get(".DBus")
    print(f"Starting service version {soundcraft.__version__}...")

    # Give the D-Bus a few seconds to notice the new service file
    timeout = 5
    while True:
        try:
            dbus_service.StartServiceByName(BUSNAME, 0)
            break  # service has been started, no need to try again
        except GLibError:
            # If the bus has not recognized the service config file
            # yet, the service is not bus activatable yet and thus the
            # GLibError will happen.
            if timeout == 0:
                raise
            timeout = timeout - 1

            time.sleep(1)
            continue  # starting service has failed, but try again

    service_version = bus.get(BUSNAME).version
    print(f"Version running: {service_version}")
    print("D-Bus installation is complete")
    print(f"Run {const.BASE_EXE_GUI} or {const.BASE_EXE_CLI} as a regular user")


def install_xdg():
    datadir = find_datadir()
    print("Using datadir", datadir)
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
                scalable_icondir = datadir / "icons/hicolor/scalable/apps"
                scalable_icondir.mkdir(parents=True, exist_ok=True)
                shutil.copy(src, scalable_icondir)
    print("Installed all XDG application launcher files")


def install():
    install_dbus()
    install_xdg()


def uninstall_dbus():
    dbus1_root = find_datadir() / "dbus-1"
    print(f"Using dbus-1 config root {dbus1_root}")
    bus = pydbus.SystemBus()
    dbus_service = bus.get(".DBus")
    if not dbus_service.NameHasOwner(BUSNAME):
        print("Service not running")
    else:
        service = bus.get(BUSNAME)
        service_version = service.version
        print(f"Shutting down service version {service_version}")
        service.Shutdown()
        print("Stopped")

    sources = findDataFiles("dbus-1")
    for (srcpath, files) in sources.items():
        for f in files:
            path = dbus1_root / f
            print(f"Removing {path}")
            try:
                path.unlink()
            except Exception as e:
                print(e)
    print("D-Bus service is unregistered")


def uninstall_xdg():
    datadir = find_datadir()
    print("Using datadir", datadir)
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
                scalable_icondir = datadir / "icons/hicolor/scalable/apps"
                svg = scalable_icondir / f.name
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
        install()
    elif args.uninstall:
        uninstall()
