import soundcraft.notepad
from .cli import show
from . import __version__
try:
    from gi.repository import GLib
except ModuleNotFoundError:
    print("\nThe PyGI library must be installed from your distribution; usually called python-gi, python-gobject, or pygobject\n")
    raise
from pydbus import SystemBus

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

def autodetect():
    bus = SystemBus()
    return bus.get("soundcraft.utils.notepad", "/soundcraft/utils/notepad/0")
