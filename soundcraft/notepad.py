import usb.core
import array
import enum

class NotepadBase:
    def __init__(self, idProduct):
        self.dev = usb.core.find(idVendor=0x05fc, idProduct=idProduct)

    def found(self):
        return self.dev is not None

    def switchChannel(self, channel):
        assert self.found()
        print(f"Switching USB audio input to {channel.name}")
        #0 => 0x00 00 04 00 00 00 00 00
        #1 => 0x00 00 04 00 01 00 00 00
        message = array.array('B', 
                [0x00, 0x00, 0x04, 0x00,
                 channel, 0x00, 0x00, 0x00])
        print(f"Sending {message}")
        result = self.dev.ctrl_transfer(0x40, 16, 0, 0, message)

    def fetchInfo(self):
        assert self.found()
        # TODO: Decode these?
        # Unfortunately, inspection shows none of the data here
        # corresponds to thr current channel selection
        self.info1 = self.dev.ctrl_transfer(0xa1, 1, 0x0100, 0x2900, 256)
        self.info2 = self.dev.ctrl_transfer(0xa1, 2, 0x0100, 0x2900, 256)

    def name(self):
        return self.__class__.__name__

    def parseChannel(self, string):
        channels = self.Channels
        try:
            chnum = int(string)
            return channels(chnum)
        except ValueError:
            try:
                return channels[string]
            except KeyError:
                for c in channels:
                    if string in c.name:
                        return c
        return None

class Notepad_12fx(NotepadBase):
    def __init__(self):
        super().__init__(0x0032)

    class Channels(enum.IntEnum):
        INPUT_3_4 = 0
        INPUT_5_6 = 1
        INPUT_7_8 = 2
        MASTER_L_R  = 3

class Notepad_8fx(NotepadBase):
    def __init__(self):
        # TODO: What is the idProduct of the Notepad 8fx?
        super().__init__(self, 0x0000)

    class Channels(enum.IntEnum):
        # TODO: Confirm this mapping on real hardware
        INPUT_1_2 = 0
        INPUT_3_4 = 1
        INPUT_5_6 = 2
        MASTER_L_R  = 3

class Notepad_5(NotepadBase):
    def __init__(self):
        # TODO: What is the idProduct of the Notepad 5?
        super().__init__(self, 0x0000)

    class Channels(enum.IntEnum):
        # TODO: Confirm this mapping on real hardware
        INPUT_1_2 = 0
        INPUT_2_3 = 1
        INPUT_4_5 = 2
        MASTER_L_R  = 3

