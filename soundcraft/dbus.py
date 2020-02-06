import soundcraft
import soundcraft.notepad
import argparse
import os.path
import sys
from string import Template
try:
    import gi
except ModuleNotFoundError:
    print("\nThe PyGI library must be installed from your distribution; usually called python-gi, python-gobject, or pygobject\n")
    raise
gi.require_version('GUdev', '1.0')
from gi.repository import GLib
from gi.repository import GUdev
from pydbus import SystemBus

def objPath(idx):
    return f"/soundcraft/utils/notepad/{idx}"

BUSNAME='soundcraft.utils.notepad'

class DeviceList(object):
    """
      <node>
        <interface name='soundcraft.utils.notepad'>
          <property name='version' type='s' access='read' />
        </interface>
      </node>
    """

    # TODO: Should also be an org.freedesktop.ObjectManager
    @property
    def version(self):
        return soundcraft.__version__

class NotepadDbus(object):
    """
      <node>
        <interface name='soundcraft.utils.notepad.device'>
          <property name='name' type='s' access='read' />
          <property name='fixedRouting' type='a{ss}' access='read' />
          <property name='routingTarget' type='s' access='read' />
          <property name='sources' type='as' access='read' />
          <property name='routingSource' type='s' access='readwrite' />
        </interface>
      </node>
    """

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

class Service:
    def __init__(self):
        self.dev = None
        self.object = None
        self.bus = SystemBus()
        self.busname = self.bus.publish(BUSNAME, DeviceList())
        self.udev = GUdev.Client(subsystems = ["usb/usb_device"])
        self.udev.connect('uevent', self.uevent)
        self.loop = GLib.MainLoop()

    def run(self):
        self.tryRegister()
        if not self.hasDevice():
            print(f"Waiting for one to arrive...")
        self.loop.run()

    def tryRegister(self):
        if self.hasDevice():
            print(f"There is already a {self.dev.name} on the bus at {objPath(0)}")
            return
        self.dev = soundcraft.notepad.autodetect()
        if self.dev is None:
            print(f"No recognised device was found")
            return
        self.object = self.bus.register_object(objPath(0), NotepadDbus(self.dev), None)
        print(f"Presenting {self.dev.name} on the system bus as {objPath(0)}")
        return

    def hasDevice(self):
        return self.object is not None

    def unregister(self):
        if not self.hasDevice():
            return
        print(f"Removed {self.dev.name} AKA {objPath(0)} from the system bus")
        self.object.unregister()
        self.object = None
        self.dev = None

    def uevent(self, observer, action, device):
        if action == 'add':
            idVendor = device.get_property('ID_VENDOR_ID')
            idProduct = device.get_property('ID_PRODUCT_ID')
            if idVendor == "05fc":
                print(f"Checking new Soundcraft device ({idVendor}:{idProduct})...")
                self.tryRegister()
                if not self.hasDevice():
                    print(f"Contact the developer for help adding support for your advice")
        elif action == 'remove':
            # UDEV adds leading 0s to decimal numbers.  They're not octal.  Why??
            busnum = int(device.get_property('BUSNUM').lstrip("0"))
            devnum = int(device.get_property('DEVNUM').lstrip("0"))
            if busnum == self.dev.dev.bus and devnum == self.dev.dev.address:
                self.unregister()

def findDbusFiles():
    result = {}
    modulepaths = soundcraft.__path__
    for path in modulepaths:
        dbusdatapath = os.path.join(path, 'data/dbus-1')
        result[dbusdatapath] = []
        for path, dirs, files in os.walk(dbusdatapath):
            if not files:
                continue
            for fname in files:
                relative = os.path.relpath(os.path.join(path, fname), start=dbusdatapath)
                result[dbusdatapath].append(relative)
    return result

def serviceExePath():
    exename = sys.argv[0]
    exename = os.path.abspath(exename)
    if exename.endswith(".py"):
        raise ValueError("Running setup out of a module-based execution is not supported")
    return exename

def setup(cfgroot="/usr/share/dbus-1"):
    templateData = {
        'dbus_service_bin': serviceExePath(),
        'busname': BUSNAME,
    }
    sources = findDbusFiles()
    for (srcpath, files) in sources.items():
        for fname in files:
            src = os.path.join(srcpath, fname)
            dst = os.path.join(cfgroot, fname)
            print(f"Installing {src} -> {dst}")
            with open(src, "r") as srcfile:
                srcTemplate = Template(srcfile.read())
                with open(dst, "w") as dstfile:
                    dstfile.write(srcTemplate.substitute(templateData))

def autodetect():
    try:
        bus = SystemBus()
        return bus.get(BUSNAME, objPath(0))
    except KeyError:
        return None

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--setup", help="Set up the dbus configuration in /usr/share/dbus-1 (Must be run as root)", action="store_true")
    args = parser.parse_args()
    if args.setup:
        setup()
    else:
        service = Service()
        service.run()

if __name__ == '__main__':
    main()
