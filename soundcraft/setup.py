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


import abc
import argparse
import shutil
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
    return exePath().parent / const.BASE_EXE_SERVICE


def exePath():
    exename = Path(sys.argv[0]).resolve()
    if exename.suffix == ".py":
        raise ValueError(
            "Running setup out of a module-based execution is not supported"
        )
    return exename


def find_datadir():
    exe_path = exePath()
    # print("exe_path", exe_path)
    for prefix in [Path("/usr/local"), Path("/usr"), Path("~/.local").expanduser()]:
        for sx_dir in ["bin", "sbin", "libexec"]:
            for sx in [const.BASE_EXE_SETUP]:
                sx_path = prefix / sx_dir / sx
                # print("sx_path", sx_path)
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
    raise ValueError(f"Exe path is not supported: {exe_path!r}")


class AbstractSetup(metaclass=abc.ABCMeta):
    def __init__(self):
        self.datadir = find_datadir()
        # print(f"Using datadir {self.datadir}")

    @abc.abstractmethod
    def install(self):
        pass  # AbstractSetup.install()

    @abc.abstractmethod
    def uninstall(self):
        pass  # AbstractSetup.uninstall()


class SetupDBus(AbstractSetup):
    def __init__(self):
        super(SetupDBus, self).__init__()
        self.service_dst = self.datadir / "dbus-1/services" / f"{BUSNAME}.service"

    def install(self):
        templateData = {
            "dbus_service_bin": str(serviceExePath()),
            "busname": BUSNAME,
        }

        sources = findDataFiles("dbus-1")
        for (srcpath, files) in sources.items():
            for f in files:
                src = srcpath / f
                if src.suffix == ".service":
                    print("Installing", self.service_dst)
                    self.service_dst.parent.mkdir(
                        mode=0o755, parents=True, exist_ok=True
                    )
                    srcTemplate = Template(src.read_text())
                    self.service_dst.write_text(srcTemplate.substitute(templateData))
                    self.service_dst.chmod(mode=0o644)

        print("Starting D-Bus service as a test...")

        bus = pydbus.SessionBus()
        dbus_service = bus.get(".DBus")
        print(f"Installer version: {soundcraft.__version__}")

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

        our_service = bus.get(BUSNAME)
        service_version = our_service.version
        print(f"Service   version: {service_version}")

        print("Shutting down session D-Bus service...")
        # As the service should either be running at this time or
        # at the very least be bus activatable, we do not catch
        # any exceptions while shutting it down because we want to
        # see any exceptions if they happen.
        our_service.Shutdown()
        print("Session D-Bus service has been shut down")

        print("D-Bus installation is complete")
        print(f"Run {const.BASE_EXE_GUI} or {const.BASE_EXE_CLI} as a regular user")

    def uninstall(self):
        bus = pydbus.SessionBus()
        dbus_service = bus.get(".DBus")
        if not dbus_service.NameHasOwner(BUSNAME):
            print("D-Bus service not running")
        else:
            service = bus.get(BUSNAME)
            service_version = service.version
            print(f"Shutting down D-Bus service version {service_version}")
            service.Shutdown()
            print("Session D-Bus service stopped")

        print(f"Removing {self.service_dst}")
        try:
            self.service_dst.unlink()
        except FileNotFoundError:
            pass  # No service file to remove

        print("D-Bus service is unregistered")


class SetupXDGDesktop(AbstractSetup):

    # FIXME05: Find out whether `xdg-desktop-menu` and `xdg-desktop-icon`
    #          must be run after all. Fedora Packaging docs suggest so.

    def install(self):
        sources = findDataFiles("xdg")
        for (srcpath, files) in sources.items():
            for f in files:
                src = srcpath / f
                if src.suffix == ".desktop":
                    application_dir = self.datadir / "applications"
                    dst = application_dir / f"{const.APP_ICON}.desktop"
                    templateData = {
                        "gui_bin": exePath().parent / const.BASE_EXE_GUI,
                        "APP_ICON": const.APP_ICON,
                    }
                    srcTemplate = Template(src.read_text())
                    print("Installing", dst)
                    dst.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
                    dst.write_text(srcTemplate.substitute(templateData))
                    dst.chmod(mode=0o644)
                elif src.suffix == ".png":
                    size_suffix = src.suffixes[-2]
                    assert size_suffix.startswith(".")
                    size = int(size_suffix[1:], 10)
                    dst = self.icondir(size) / f"{const.APP_ICON}.png"
                    print("Installing", dst)
                    dst.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
                    shutil.copy(src, dst)
                    dst.chmod(mode=0o644)
                elif src.suffix == ".svg":
                    dst = self.icondir() / f"{const.APP_ICON}.svg"
                    print("Installing", dst)
                    dst.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
                    shutil.copy(src, dst)
                    dst.chmod(mode=0o644)
        print("Installed all XDG application launcher files")

    def uninstall(self):
        sources = findDataFiles("xdg")
        for (srcpath, files) in sources.items():
            for f in files:
                src = srcpath / f
                if src.suffix == ".desktop":
                    application_dir = self.datadir / "applications"
                    dst = application_dir / f"{const.APP_ICON}.desktop"
                    print(f"Uninstalling {dst}")
                    try:
                        dst.unlink()
                    except FileNotFoundError:
                        pass  # No dst file to remove
                elif src.suffix == ".png":
                    size_suffix = src.suffixes[-2]
                    assert size_suffix.startswith(".")
                    size = int(size_suffix[1:], 10)
                    dst = self.icondir(size) / f"{const.APP_ICON}.png"
                    print(f"Uninstalling {dst}")
                    try:
                        dst.unlink()
                    except FileNotFoundError:
                        pass  # No dst file to remove
                elif src.suffix == ".svg":
                    dst = self.icondir() / f"{const.APP_ICON}.svg"
                    print(f"Uninstalling {dst}")
                    try:
                        dst.unlink()
                    except FileNotFoundError:
                        pass  # No dst file to remove
        print("Removed all XDG application launcher files")

    def icondir(self, size=None):
        if size is None:
            return self.datadir / "icons/hicolor/scalable/apps"
        else:
            return self.datadir / f"icons/hicolor/{size}x{size}/apps"


class SetupEverything(AbstractSetup):
    def __init__(self):
        super(SetupEverything, self).__init__()
        self.everything = []

    def add(self, thing):
        self.everything.append(thing)

    def install(self):
        for thing in self.everything:
            thing.install()

    def uninstall(self):
        for thing in reversed(self.everything):
            thing.uninstall()


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

    everything = SetupEverything()
    everything.add(SetupDBus())
    everything.add(SetupXDGDesktop())

    if args.install:
        everything.install()
    elif args.uninstall:
        everything.uninstall()
