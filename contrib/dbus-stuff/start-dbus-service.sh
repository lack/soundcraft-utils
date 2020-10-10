#!/bin/sh

busctl="busctl --user"

busname="soundcraft.utils.notepad"
devinterface="soundcraft.utils.notepad.device"
devpath="/soundcraft/utils/notepad/0"

set -xe

# Start the soundcraft-utils D-Bus service via bus activation on the
# session bus.

# dbus-send --session --print-reply --dest=org.freedesktop.DBus \
#	  /org/freedesktop/DBus org.freedesktop.DBus.StartServiceByName \
#	  "string:${busname}" uint32:0

# Note that busctl has beautiful bash shell completion for bus names
# etc.

${busctl} call org.freedesktop.DBus /org/freedesktop/DBus \
       org.freedesktop.DBus StartServiceByName su "${busname}" 0

sleep 2

# See what objects the soundcraft-utils D-Bus service exposes on the
# session bus.

${busctl} tree "${busname}"
${busctl} --no-pager introspect "${busname}" "$devpath"

${busctl} get-property "${busname}" "$devpath" "$devinterface" sources

${busctl} get-property "${busname}" "$devpath" "$devinterface" routingSource

${busctl} set-property "${busname}" "$devpath" "$devinterface" s MASTER_L_R
