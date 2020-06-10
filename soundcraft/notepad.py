import array
import enum
import json
import os

import usb.core


def autodetect():
    for devType in ("12fx", "8fx", "5"):
        dev = eval(f"Notepad_{devType}()")
        if dev.found():
            return dev


class NotepadBase:
    def __init__(
        self,
        idProduct,
        routingTarget,
        stateDir="/var/lib/soundcraft-utils",
        fixedRouting={},
    ):
        self.routingTarget = routingTarget
        self.fixedRouting = fixedRouting
        self.stateDir = stateDir
        self.dev = usb.core.find(idVendor=0x05FC, idProduct=idProduct)
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
        # 0 => 0x00 00 04 00 00 00 00 00
        # 1 => 0x00 00 04 00 01 00 00 00
        message = array.array("B", [0x00, 0x00, 0x04, 0x00, source, 0x00, 0x00, 0x00])
        print(f"Sending {message}")
        self.dev.ctrl_transfer(0x40, 16, 0, 0, message)
        self.state["source"] = source
        self._saveState()

    @property
    def sources(self):
        return [x.name for x in self.Sources]

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

    def _parseSourcename(self, string):
        sources = self.Sources
        try:
            num = int(string)
            return sources(num)
        except ValueError:
            try:
                return sources[string]
            except KeyError:
                for source in sources:
                    if string in source.name:
                        return source
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


class Notepad_12fx(NotepadBase):
    def __init__(self):
        super().__init__(
            idProduct=0x0032,
            routingTarget="capture_3_4",
            fixedRouting={"capture_1_2": "INPUT_1_2"},
        )

    class Sources(enum.IntEnum):
        INPUT_3_4 = 0
        INPUT_5_6 = 1
        INPUT_7_8 = 2
        MASTER_L_R = 3


class Notepad_8fx(NotepadBase):
    def __init__(self):
        super().__init__(idProduct=0x0031, routingTarget="capture_1_2")

    class Sources(enum.IntEnum):
        INPUT_1_2 = 0
        INPUT_3_4 = 1
        INPUT_5_6 = 2
        MASTER_L_R = 3


class Notepad_5(NotepadBase):
    def __init__(self):
        # TODO: What is the idProduct of the Notepad 5?
        super().__init__(idProduct=0x0000, routingTarget="capture_1_2")

    class Sources(enum.IntEnum):
        # TODO: Confirm this mapping on real hardware
        INPUT_1_2 = 0
        INPUT_2_3 = 1
        INPUT_4_5 = 2
        MASTER_L_R = 3
