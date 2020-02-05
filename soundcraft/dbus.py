import soundcraft.notepad
from .cli import show
from . import __version__
try:
    from gi.repository import GLib
except ModuleNotFoundError:
    print("\nThe PyGI library must be installed from your distribution; usually called python-gi, python-gobject, or pygobject\n")
    raise
from pydbus import SystemBus
import argparse
import os.path
import sys
from string import Template

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
        return __version__

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

def service():
    dev = soundcraft.notepad.autodetect()
    if dev is None:
        # TODO: Wait for udev to signal that a device has appeared?
        raise RuntimeError("No device found")
    bus = SystemBus()
    bus.publish("soundcraft.utils.notepad", DeviceList(), ("0", NotepadDbus(dev)))
    print(f"Presenting {dev.name} on the system bus as \"/soundcraft/utils/notepad/0\"")
    loop = GLib.MainLoop()
    loop.run()

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
        'dbus_service_bin': serviceExePath()
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
    bus = SystemBus()
    return bus.get("soundcraft.utils.notepad", "/soundcraft/utils/notepad/0")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--setup", help="Set up the dbus configuration in /usr/share/dbus-1 (Must be run as root)", action="store_true")
    args = parser.parse_args()
    if args.setup:
        setup()
    else:
        service()

if __name__ == '__main__':
    main()
