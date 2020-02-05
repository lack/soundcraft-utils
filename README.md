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

Installation
------------

Install from pip:
```bash
sudo pip install soundcraft-utils
```

Set up the DBUS service so it can be auto-started by root as needed:
```bash
sudo soundcraft_dbus_service --setup
```

Usage
-----

List possible channel routing choices:
```bash
soundcraft_ctl -l
```

Set channel routing:
```bash
soundcraft_ctl -s <number>
```

TODO
----

- Multiple device support
- Add additional model support
    - Notepad-8FX should be easy, once I know what the USB idProduct field is (plus I'd need help from someone with a Notepad-8FX for testing)
    - Notepad-5 likewise, same constraints
- Auto-duck feature
- Firmware upgrade
- GUI?  People like those, right?
