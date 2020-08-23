#!/bin/sh

busname="soundcraft.utils.notepad"

set -xe

# Start the soundcraft-utils dbus service via bus activation on the system bus

# dbus-send --system --print-reply --dest=org.freedesktop.DBus \
#	  /org/freedesktop/DBus org.freedesktop.DBus.StartServiceByName \
#	  "string:${busname}" uint32:0

busctl call org.freedesktop.DBus /org/freedesktop/DBus \
       org.freedesktop.DBus StartServiceByName su "${busname}" 0

sleep 2

# See what objects the soundcraft-utils dbus service exposes on the system bus
# Note that busctl has beautiful bash shell completion for bus names etc.

busctl tree "${busname}"
busctl --no-pager introspect "${busname}" /soundcraft/utils/notepad/0

busctl get-property "${busname}" /soundcraft/utils/notepad/0 \
       soundcraft.utils.notepad.device sources

busctl get-property "${busname}" /soundcraft/utils/notepad/0 \
       soundcraft.utils.notepad.device routingSource

busctl set-property "${busname}" /soundcraft/utils/notepad/0 \
       soundcraft.utils.notepad.device routingSource s INPUT_7_8
