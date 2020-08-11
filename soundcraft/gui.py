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

import sys
import traceback
from pathlib import Path

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from gi.repository import Gio

import soundcraft
from soundcraft.dbus import Client, DbusInitializationError, VersionIncompatibilityError


def iconFile():
    modulepaths = soundcraft.__path__
    for path in modulepaths:
        png = Path(path) / "data" / "xdg" / "soundcraft-utils.png"
        if png.exists():
            return str(png)
    return None


class Main(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(title="Soundcraft-utils", application=app)
        self.app = app
        icon = iconFile()
        if icon is not None:
            self.set_default_icon_from_file(icon)
        self.connect("destroy", self.app.quit_cb)
        self.grid = None
        self.dev = None
        self.setNoDevice()
        try:
            self.dbus = Client(added_cb=self.deviceAdded, removed_cb=self.deviceRemoved)
        except DbusInitializationError as e:
            print(f"Startup error: {str(e)}")
            self._startupFailure("Could not start soundcraft_gui", str(e))
            raise e
        except Exception as e:
            print("Unexpected exception at gui startup")
            traceback.print_exc()
            self._startupFailure(f"Unexpected exception {e.__class__.__name__}", str(e))
            raise e
        self.dbus.serviceDisconnected.connect(self.dbusDisconnect)
        self.dbus.serviceConnected.connect(self.dbusReconnect)

    def _startupFailure(self, title, message):
        dialog = Gtk.MessageDialog(
            parent=self,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text=title,
        )
        dialog.format_secondary_text(message)
        dialog.run()

    def dbusDisconnect(self):
        self.setNoDevice()

    def dbusReconnect(self):
        try:
            self.dbus.ensureServiceVersion()
        except VersionIncompatibilityError:
            self._startupFailure(
                "Dbus service version incompatibility",
                "Restart of this gui application is required",
            )
            self.app.quit()
            # Todo: Can we relaunch ourselves?

    def setDevice(self, dev):
        if self.dev is not None:
            if self.dev._path == dev._path:
                # This already is our device
                return
        if self.grid is not None:
            self.remove(self.grid)
        self.dev = dev
        dev.onPropertiesChanged = self.reset
        self.grid = Gtk.Grid()
        self.add(self.grid)
        self.row = 0
        self.addHeading(self.dev.name)
        self.addSep()
        for (target, source) in self.dev.fixedRouting.items():
            self.addRow(target, source)
            self.addSep()
        self.sourceCombo = Gtk.ComboBoxText()
        self.sourceCombo.set_entry_text_column(0)
        for source in self.dev.sources:
            self.sourceCombo.append_text(source)
        self.sourceCombo.connect("changed", self.selectionChanged)
        self.addRow(self.dev.routingTarget, self.sourceCombo)
        self.addActions()
        self.reset()
        self.show_all()

    def setNoDevice(self):
        self.dev = None
        if self.grid is not None:
            self.remove(self.grid)
        self.grid = Gtk.Grid()
        self.add(self.grid)
        self.row = 0
        self.addHeading("No device found")
        self.show_all()

    def deviceAdded(self, dev):
        print(f"Added {dev._path}")
        self.setDevice(dev)

    def deviceRemoved(self, path):
        print(f"Removed {path}")
        if self.dev is not None:
            if self.dev._path != path:
                # Not our device
                return
        self.setNoDevice()

    def addHeading(self, text):
        section = Gtk.Label(label=None, margin=10, halign=Gtk.Align.START)
        section.set_markup(f"<b>{text}</b>")
        self.grid.attach(section, 0, self.row, 3, 1)
        self.row += 1

    def addRow(self, left, right):
        if type(left) == str:
            left = Gtk.Label(label=left)
        left.set_margin_top(10)
        left.set_margin_bottom(10)
        left.set_margin_start(10)
        left.set_margin_end(2)
        self.grid.attach(left, 0, self.row, 1, 1)
        self.grid.attach(
            Gtk.Image.new_from_icon_name("pan-start", Gtk.IconSize.BUTTON),
            1,
            self.row,
            1,
            1,
        )
        if type(right) == str:
            right = Gtk.Label(label=right)
        right.set_margin_top(10)
        right.set_margin_bottom(10)
        right.set_margin_end(10)
        right.set_margin_start(2)
        right.set_halign(Gtk.Align.START)
        self.grid.attach(right, 2, self.row, 1, 1)
        self.row += 1

    def addSep(self):
        self.grid.attach(
            Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL), 0, self.row, 3, 1
        )
        self.row += 1

    def addActions(self):
        self.actions = Gtk.ActionBar()
        self.grid.attach(self.actions, 0, self.row, 3, 1)
        self.applyButton = Gtk.Button.new_with_mnemonic("_Apply")
        self.resetButton = Gtk.Button.new_with_mnemonic("_Reset")
        self.actions.pack_end(self.applyButton)
        self.actions.pack_end(self.resetButton)
        self.resetButton.connect("clicked", self.reset)
        self.applyButton.connect("clicked", self.apply)

    def selectionChanged(self, comboBox):
        self.nextSelection = comboBox.get_active_text()
        self.setActionsEnabled(self.nextSelection != self.dev.routingSource)

    def apply(self, button=None):
        print(f"Setting routing source to {self.nextSelection}")
        self.dev.routingSource = self.nextSelection
        self.setActionsEnabled(False)

    def reset(self, button=None, *args, **kwargs):
        for (i, source) in enumerate(self.dev.sources):
            if self.dev.routingSource == source:
                self.sourceCombo.set_active(i)
        self.setActionsEnabled(False)

    def setActionsEnabled(self, enabled):
        self.applyButton.set_sensitive(enabled)
        self.resetButton.set_sensitive(enabled)


class About(Gtk.AboutDialog):
    def __init__(self):
        super().__init__(
            program_name="soundcraft-utils",
            version=soundcraft.__version__,
            comments="Linux Utilities for Soundcraft Mixers",
            license_type=Gtk.License.MIT_X11,
            website="https://github.com/lack/soundcraft-utils",
            website_label="Github page",
            authors=[
                "Jim Ramsay <i.am@jimramsay.com> - Author",
                "Christoph <soffioalcuore@posteo.net> - Testing and suggestions",
                "Pete Merges <pdmerges@gmail.com> - Notepad-8FX support and testing",
                "Viktor Mastoridis <viktor.mastoridis@gmail.com> - Notepad-5 support and testing",
            ],
            artists=["Flat Icons https://www.flaticon.com/authors/flat-icons"],
        )
        self.connect("response", self.close_cb)

    def close_cb(self, action, parameter):
        action.close()


class App(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="soundcraft.utils")
        self.window = None

    def do_activate(self):
        if self.window is not None:
            return
        try:
            self.window = Main(self)
        except DbusInitializationError:
            self.quit()
        except Exception:
            print("Unexpected exception at gui startup")
            traceback.print_exc()
            self.quit()

    def about_cb(self, action, parameter):
        about = About()
        about.show()

    def quit_cb(self, *args, **kwargs):
        self.quit()

    def do_startup(self):
        Gtk.Application.do_startup(self)
        self.set_app_menu(Gio.Menu())
        self.addAppmenu("About", self.about_cb)
        self.addAppmenu("Quit", self.quit_cb)

    def addAppmenu(self, name, cb):
        actionName = name.lower()
        self.get_app_menu().append(name, f"app.{actionName}")
        action = Gio.SimpleAction(name=actionName)
        action.connect("activate", cb)
        self.add_action(action)


def main():
    app = App()
    sys.exit(app.run(sys.argv))


if __name__ == "__main__":
    main()
