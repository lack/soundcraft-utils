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

import array
import enum
import json
import os

import usb.core


DEFAULT_STATEDIR = "/var/lib/soundcraft-utils"
HARMAN_USB = 0x05FC


def autodetect(stateDir=DEFAULT_STATEDIR):
    for devType in ("12fx", "8fx", "5"):
        dev = eval(f"Notepad_{devType}(stateDir=stateDir)")
        if dev.found():
            return dev


class NotepadBase:
    def __init__(
        self,
        idProduct,
        routingTarget,
        stateDir=DEFAULT_STATEDIR,
        fixedRouting=[],
        playbackLabels=[],
    ):
        self.routingTarget = routingTarget
        self.fixedRouting = fixedRouting
        self.playbackLabels = playbackLabels
        self.stateDir = stateDir
        self.dev = usb.core.find(idVendor=HARMAN_USB, idProduct=idProduct)
        if self.dev is not None:
            major = self.dev.bcdDevice >> 8
            minor = self.dev.bcdDevice & 0xFF
            try:
                self.product = self.dev.product
            except Exception:
                # Fall-back to class name, since reading the product over USB requires write access
                self.product = self.__class__.__name__
            self.fwVersion = f"{major}.{minor}"
            self.stateFile = f"{stateDir}/{self.product}.state"
            self.state = {}
            self._loadState()

    def found(self):
        return self.dev is not None

    def resetState(self):
        storedSource = self.routingSource
        if storedSource == "UNKNOWN":
            return
        self.routingSource = storedSource

    @property
    def routingSource(self):
        if "source" not in self.state:
            return "UNKNOWN"
        return self.Sources(self.state["source"]).name

    @routingSource.setter
    def routingSource(self, request):
        assert self.found()
        source = self._parseSourcename(request)
        if source is None:
            raise ValueError(f"Requested input {request} is not a valid choice")
        print(f"Switching USB audio input to {source.name}")
        # Reverse engineered via Wireshark on Windows
        # 0 => 0x00 00 04 00 00 00 00 00
        # 1 => 0x00 00 04 00 01 00 00 00
        #        Change this -^
        message = array.array("B", [0x00, 0x00, 0x04, 0x00, source, 0x00, 0x00, 0x00])
        print(f"Sending {message}")
        self.dev.ctrl_transfer(0x40, 16, 0, 0, message)
        self.state["source"] = source
        self._saveState()

    @property
    def sources(self):
        return {x.name: self.Label[x] for x in self.Sources}

    @property
    def name(self):
        return f"{self.product} (fw v{self.fwVersion})"

    def fetchInfo(self):
        assert self.found()
        # TODO: Decode these?
        # Unfortunately, inspection shows none of the data here
        # corresponds to thr current source selection
        self.info1 = self.dev.ctrl_transfer(0xA1, 1, 0x0100, 0x2900, 256)
        self.info2 = self.dev.ctrl_transfer(0xA1, 2, 0x0100, 0x2900, 256)

    def _parseSourcename(self, request):
        sources = self.Sources
        if isinstance(request, self.Sources):
            return request
        if isinstance(request, int):
            return sources(request)
        try:
            num = int(request)
            return self._parseSourcename(num)
        except ValueError:
            try:
                return sources[request]
            except KeyError:
                for source in sources:
                    # This could be better; maybe ensure it's a unique substring?
                    if str(request) in source.name:
                        return source
        except Exception:
            pass
        return None

    def _saveState(self):
        try:
            os.makedirs(self.stateDir, exist_ok=True)
            with open(self.stateFile, "w") as fh:
                fh.write(json.dumps(self.state, sort_keys=True, indent=4))
        except Exception as e:
            print(f"Warning: Could not write state file: {e}")

    def _loadState(self):
        try:
            with open(self.stateFile, "r") as fh:
                self.state = json.loads(fh.read())
        except Exception:
            pass


def label_pair(base, start):
    return (f"{base}{start}", f"{base}{start+1}")


def stereo_label(base):
    return (f"{base} L", f"{base} R")


class Notepad_12fx(NotepadBase):
    def __init__(self, **kwargs):
        super().__init__(
            idProduct=0x0032,
            routingTarget=label_pair("capture_", 3),
            fixedRouting=[(label_pair("capture_", 1), label_pair("Mic/Line ", 1))],
            playbackLabels=[
                (label_pair("playback_", 1), stereo_label("Stereo 9/10")),
                (label_pair("playback_", 3), stereo_label("USB-3/4")),
            ],
            **kwargs,
        )

    class Sources(enum.IntEnum):
        INPUT_3_4 = 0
        INPUT_5_6 = 1
        INPUT_7_8 = 2
        MASTER_L_R = 3

    Label = {
        Sources.INPUT_3_4: label_pair("Mic/Line ", 3),
        Sources.INPUT_5_6: stereo_label("Stereo 5/6"),
        Sources.INPUT_7_8: stereo_label("Stereo 7/8"),
        Sources.MASTER_L_R: stereo_label("Mix"),
    }


class Notepad_8fx(NotepadBase):
    def __init__(self, **kwargs):
        super().__init__(
            idProduct=0x0031,
            routingTarget=label_pair("capture_", 1),
            playbackLabels=[(label_pair("playback_", 1), stereo_label("Stereo 7/8"))],
            **kwargs,
        )

    class Sources(enum.IntEnum):
        INPUT_1_2 = 0
        INPUT_3_4 = 1
        INPUT_5_6 = 2
        MASTER_L_R = 3

    Label = {
        Sources.INPUT_1_2: label_pair("Mic/Line ", 1),
        Sources.INPUT_3_4: stereo_label("Stereo 3/4"),
        Sources.INPUT_5_6: stereo_label("Stereo 5/6"),
        Sources.MASTER_L_R: stereo_label("Mix"),
    }


class Notepad_5(NotepadBase):
    def __init__(self, **kwargs):
        super().__init__(
            idProduct=0x0030,
            routingTarget=label_pair("capture_", 1),
            playbackLabels=[(label_pair("playback_", 1), stereo_label("Stereo 4/5"))],
            **kwargs,
        )

    class Sources(enum.IntEnum):
        MONO_1_MONO_2 = 0
        STEREO_2_3 = 1
        STEREO_4_5 = 2
        MASTER_L_R = 3

    Label = {
        Sources.MONO_1_MONO_2: ("Mic/Line 1", "Mono Line 2"),
        Sources.STEREO_2_3: stereo_label("Stereo 2/3"),
        Sources.STEREO_4_5: stereo_label("Stereo 4/5"),
        Sources.MASTER_L_R: stereo_label("Mix"),
    }
