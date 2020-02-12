Linux Utilities for Soundcraft Mixers
=====================================

[Soundcraft Notepad](https://www.soundcraft.com/en/product_families/notepad-series)
mixers are pretty nice small-sized mixer boards with Harmon USB I/O
built-in.  While the USB audio works great in alsa without any
additional configuration needed, there are some advanced features
available to the Windows driver that have no Linux equivalent.
Most importantly, the USB routing for the capture channels is
software-controlled, and requires an additional utility.  For
example, by default the Notepad-12FX sends inputs 3 and 4 to USB
capture channels 3 and 4, but can be changed to input 5&6, input
7&8, or the Master L&R outputs.  This tool aims to give this same
software control of the USB capture channel routing to Linux users.

Supported models:
- Notepad-12FX

Prerequisites
-------------

The dbus service relies on [PyGObject](https://pygobject.readthedocs.io/en/latest/index.html)
which is not available via pypi without a lot of dev libraries for
it to compile against.  It is usually easier to install separately
using your distribution's package installation tools.  Under Ubuntu,
the following should work:

```bash
sudo apt install python3-gi
```

Installation
------------

Install from pip:

```bash
sudo pip install soundcraft-utils
```

It is not recommended to use `--user` mode and install this
system-wide so that the dbus service auto-start can reliably find the
right python libs.

Set up the DBUS service so it can access the system bus and be
auto-started on demand:

```bash
sudo soundcraft_dbus_service --setup
```

The dbus service will run as root, providing access to the underlying
USB device so the `soundcraft_ctl` user-facing part can be run by an
unprivileged account.

Usage
-----

### GUI

```bash
soundcraft_gui
```

### CLI

List possible channel routing choices:

```bash
soundcraft_ctl [--no-dbus] -l
```

Set channel routing:

```bash
soundcraft_ctl [--no-dbus] -s <number>
```

When using the `--no-dbus`, write access to the underling USB device is
required. Normally only root can do this, unless you've added some custom
udev rules.

TODO
----

- Polkit restrictions on the dbus service
- Multiple device support
- Add additional model support
    - Notepad-8FX should be easy, once I know what the USB idProduct field is (plus I'd need help from someone with a Notepad-8FX for testing)
    - Notepad-5 likewise, same constraints
- Auto-duck feature
- Firmware upgrade
