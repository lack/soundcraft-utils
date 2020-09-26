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

try:
    import gi
except ModuleNotFoundError:
    print(
        """
The PyGI library must be installed from your distribution; usually called
python-gi, python-gobject, python3-gobject, pygobject, or something similar.
"""
    )
    raise
gi.require_version("GUdev", "1.0")
from gi.repository import GLib, GUdev
from pydbus import SystemBus
from pydbus.generic import signal

import soundcraft
import soundcraft.notepad
import soundcraft.constants as const


BUSNAME = "soundcraft.utils.notepad"


class NotepadDbus(object):
    dbus = """
      <node>
        <interface name='soundcraft.utils.notepad.device'>
          <property name='name'          type='s'           access='read' />
          <property name='fixedRouting'  type='a((ss)(ss))' access='read' />
          <property name='routingTarget' type='(ss)'        access='read' />
          <property name='sources'       type='a{s(ss)}'    access='read' />
          <property name='routingSource' type='s'           access='readwrite'>
            <annotation name="org.freedesktop.DBus.Property.EmitsChangedSignal"
                        value="true"/>
          </property>
        </interface>
      </node>
    """

    InterfaceName = "soundcraft.utils.notepad.device"

    def __init__(self, dev):
        self._dev = dev

    @property
    def name(self):
        return self._dev.name

    @property
    def fixedRouting(self):
        return self._dev.fixedRouting

    @property
    def routingTarget(self):
        return self._dev.routingTarget

    @property
    def sources(self):
        return self._dev.sources

    @property
    def routingSource(self):
        return self._dev.routingSource

    @routingSource.setter
    def routingSource(self, request):
        self._dev.routingSource = request
        self.PropertiesChanged(
            self.InterfaceName, {"routingSource": self.routingSource}, []
        )

    PropertiesChanged = signal()


class Service:
    dbus = """
      <node>
        <interface name='soundcraft.utils.notepad'>
          <property name='version' type='s'  access='read' />
          <property name='devices' type='ao' access='read'>
            <annotation name="org.freedesktop.DBus.Property.EmitsChangedSignal"
                        value="true"/>
          </property>
          <signal name='Added'>
            <arg name='path' type='o'/>
          </signal>
          <signal name='Removed'>
            <arg name='path' type='o'/>
          </signal>
          <method name='Shutdown'/>
        </interface>
      </node>
    """

    InterfaceName = "soundcraft.utils.notepad"
    PropertiesChanged = signal()
    Added = signal()
    Removed = signal()

    def __init__(self):
        self.object = None
        self.bus = SystemBus()
        self.udev = GUdev.Client(subsystems=["usb/usb_device"])
        self.udev.connect("uevent", self.uevent)
        self.loop = GLib.MainLoop()
        self.busname = self.bus.publish(BUSNAME, self)

    def run(self):
        self.tryRegister()
        if not self.hasDevice():
            print("Waiting for one to arrive...")
        self.loop.run()

    @property
    def version(self):
        return soundcraft.__version__

    @property
    def devices(self):
        if self.hasDevice():
            return [self.object._path]
        return []

    def Shutdown(self):
        print("Shutting down")
        self.unregister()
        self.loop.quit()

    def objPath(self, idx):
        return f"/soundcraft/utils/notepad/{idx}"

    def tryRegister(self):
        if self.hasDevice():
            print(
                f"There is already a {self.object._wrapped._dev.name} on the bus at {self.object._path}"
            )
            return
        dev = soundcraft.notepad.autodetect()
        if dev is None:
            print("No recognised device was found")
            return
        # Reset any stored state
        dev.resetState()
        path = self.objPath(0)
        wrapped = NotepadDbus(dev)
        self.object = self.bus.register_object(path, wrapped, None)
        self.object._wrapped = wrapped
        self.object._path = path
        print(
            f"Presenting {self.object._wrapped._dev.name} on the system bus as {path}"
        )
        self.Added(path)
        self.PropertiesChanged(self.InterfaceName, {"devices": self.devices}, [])

    def hasDevice(self):
        return self.object is not None

    def unregister(self):
        if not self.hasDevice():
            return
        path = self.object._path
        print(
            f"Removed {self.object._wrapped._dev.name} AKA {path} from the system bus"
        )
        self.object.unregister()
        self.object = None
        self.PropertiesChanged(self.InterfaceName, {"devices": self.devices}, [])
        self.Removed(path)

    def uevent(self, observer, action, device):
        if action == "add":
            idVendor = int(device.get_property("ID_VENDOR_ID"), 16)
            idProduct = int(device.get_property("ID_PRODUCT_ID"), 16)
            if idVendor == soundcraft.notepad.HARMAN_USB:
                print(
                    f"Checking new Soundcraft device ({idVendor:0>4x}:{idProduct:0>4x})..."
                )
                self.tryRegister()
                if not self.hasDevice():
                    print(
                        "Contact the developer for help adding support for your device"
                    )
        elif action == "remove" and self.hasDevice():
            # UDEV adds leading 0s to decimal numbers.  They're not octal.  Why??
            busnum = int(device.get_property("BUSNUM"), 10)
            devnum = int(device.get_property("DEVNUM"), 10)
            objectdev = self.object._wrapped._dev.dev
            if busnum == objectdev.bus and devnum == objectdev.address:
                self.unregister()


class DbusInitializationError(RuntimeError):
    pass  # class DbusInitializationError


class VersionIncompatibilityError(DbusInitializationError):
    def __init__(self, serviceVersion, pid, clientVersion):
        super().__init__(
            f"Running service version {serviceVersion} (PID {pid}) is incompatible with the client version {clientVersion} - Kill and restart the D-Bus service"
        )


class DbusServiceSetupError(DbusInitializationError):
    def __init__(self):
        super().__init__(
            f"No D-Bus service found for {BUSNAME} - Run '{const.BASE_EXE_SERVICE} --setup' as root to enable it"
        )


class Client:
    MGRPATH = "/soundcraft/utils/notepad"

    def __init__(self, added_cb=None, removed_cb=None):
        self.bus = SystemBus()
        self.dbusmgr = self.bus.get(".DBus")
        self.dbusmgr.onNameOwnerChanged = self._nameChanged
        self.manager = None
        self.initManager()
        self.ensureServiceVersion(allowRestart=True)
        if removed_cb is not None:
            self.deviceRemoved.connect(removed_cb)
        if added_cb is not None:
            self.deviceAdded.connect(added_cb)
            self.autodetect()

    def initManager(self):
        try:
            self.manager = self.bus.get(BUSNAME, self.MGRPATH)
            self.manager.onAdded = self._onAdded
            self.manager.onRemoved = self._onRemoved
        except Exception as e:
            if "org.freedesktop.DBus.Error.ServiceUnknown" in e.message:
                raise DbusServiceSetupError()
            raise e

    def servicePid(self):
        return self.dbusmgr.GetConnectionUnixProcessID(BUSNAME)

    def serviceVersion(self):
        return self.manager.version

    def _canShutdown(self):
        return callable(getattr(self.manager, "Shutdown", None))

    def ensureServiceVersion(self, allowRestart=False):
        mgrVersion = self.serviceVersion()
        localVersion = soundcraft.__version__
        if mgrVersion != localVersion:
            if not self._canShutdown() or not allowRestart:
                raise VersionIncompatibilityError(
                    mgrVersion, self.servicePid(), localVersion
                )
            else:
                self.restartService(mgrVersion, localVersion)
                self.ensureServiceVersion(allowRestart=False)

    def restartService(self, mgrVersion, localVersion):
        print(
            f"Restarting soundcraft D-Bus service ({self.servicePid()}) to upgrade {mgrVersion}->{localVersion}"
        )
        self.shutdown()
        self.initManager()
        print(f"Restarted the service at {self.servicePid()}")

    def shutdown(self):
        loop = GLib.MainLoop()
        with self.serviceDisconnected.connect(loop.quit):
            self.manager.Shutdown()
            loop.run()

    serviceConnected = signal()

    serviceDisconnected = signal()

    def _nameChanged(self, busname, old, new):
        if busname != BUSNAME:
            return
        if old == "":
            print(f"New {busname} connected")
            self.serviceConnected()
        elif new == "":
            print(f"{busname} service disconnected")
            self.serviceDisconnected()

    def autodetect(self):
        devices = self.manager.devices
        if not devices:
            return None
        proxyDevice = self.bus.get(BUSNAME, devices[0])
        self.deviceAdded(proxyDevice)
        return proxyDevice

    def waitForDevice(self):
        loop = GLib.MainLoop()
        with self.manager.Added.connect(lambda path: loop.quit()):
            loop.run()
        return self.autodetect()

    deviceAdded = signal()

    def _onAdded(self, path):
        proxyDevice = self.bus.get(BUSNAME, path)
        self.deviceAdded(proxyDevice)

    deviceRemoved = signal()

    def _onRemoved(self, path):
        self.deviceRemoved(path)


def main():
    parser = argparse.ArgumentParser(description=f"The {const.PACKAGE} D-Bus service.")
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s ({const.PACKAGE}) {soundcraft.__version__}",
    )

    parser.parse_args()

    service = Service()
    service.run()
