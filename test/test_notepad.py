import array
from unittest.mock import DEFAULT, MagicMock, patch

import pytest
import usb.core
from soundcraft import notepad


class UsbCoreMock:
    def __init__(self):
        self.mockUsb = {}

    def find(self, idVendor, idProduct):
        if idVendor != 0x05FC:
            return None
        return self.mockUsb.get(idProduct, None)

    def setupDevice(self, id):
        self.mockUsb[id] = DEFAULT


@pytest.fixture
def usbCore():
    mock = UsbCoreMock()
    usb.core.find = MagicMock(side_effect=mock.find)
    return mock


def test_autodetect_none(usbCore, tmpdir):
    dev = notepad.autodetect(tmpdir)
    assert dev is None


@pytest.mark.parametrize(
    "id, expected",
    [
        (0x0032, notepad.Notepad_12fx),
        (0x0031, notepad.Notepad_8fx),
        (0x0030, notepad.Notepad_5),
    ],
)
def test_autodetect_single(usbCore, tmpdir, id, expected):
    usbCore.setupDevice(id)
    dev = notepad.autodetect(stateDir=tmpdir)
    assert isinstance(dev, expected)


@patch("usb.core.find", return_value=None)
def test_notepad_notfound(find, tmpdir):
    dev = notepad.Notepad_12fx(stateDir=tmpdir)
    assert not dev.found()
    with pytest.raises(AssertionError):
        dev.fetchInfo()
    with pytest.raises(AssertionError):
        dev.routingSource = "Anything"


def messageFor(i):
    # Reverse engineered via Wireshark on Windows
    # 0 => 0x00 00 04 00 00 00 00 00
    # 1 => 0x00 00 04 00 01 00 00 00
    #        Change this -^
    return array.array("B", [0x00, 0x00, 0x04, 0x00, i, 0x00, 0x00, 0x00])


@pytest.mark.parametrize(
    "desiredSource, expectedCtrlMessage",
    [
        (0, messageFor(0)),
        (1, messageFor(1)),
        (2, messageFor(2)),
        (3, messageFor(3)),
        ("INPUT_3_4", messageFor(0)),
        ("INPUT_5_6", messageFor(1)),
        ("INPUT_7_8", messageFor(2)),
        ("MASTER_L_R", messageFor(3)),
        ("5_6", messageFor(1)),
        (notepad.Notepad_12fx.Sources.INPUT_7_8, messageFor(2)),
    ],
)
@patch("usb.core.find")
def test_notepad_statesave(find, desiredSource, expectedCtrlMessage, tmpdir):
    usbdev = find.return_value
    usbdev.product = "TestNotepad"
    dev = notepad.Notepad_12fx(stateDir=tmpdir)
    assert dev.found()
    assert dev.routingSource == "UNKNOWN"
    dev.routingSource = desiredSource
    usbdev.ctrl_transfer.assert_called_with(0x40, 16, 0, 0, expectedCtrlMessage)
    dev2 = notepad.Notepad_12fx(stateDir=tmpdir)
    assert dev2.routingSource == dev.routingSource


@pytest.mark.parametrize("input", ["bad", -1, 512, "master_l_r", "INPUT_1_2", None])
@patch("usb.core.find")
def test_notepad_badsource(find, input, tmpdir):
    dev = notepad.Notepad_12fx(stateDir=tmpdir)
    assert dev.found()
    with pytest.raises(ValueError):
        dev.routingSource = input
