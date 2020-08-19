from unittest.mock import MagicMock

import pytest

from soundcraft import jacksync


class MockJackPort:
    def __init__(self, name, aliases):
        self.name = name
        (self._devname, self._shortname) = name.split(":", 2)
        self._aliases = aliases

    @property
    def shortname(self):
        return self._shortname

    @shortname.setter
    def shortname(self, shortname):
        assert shortname not in self._aliases
        self._shortname = shortname

    @property
    def aliases(self):
        return self._aliases

    def set_alias(self, alias):
        assert alias != self._shortname
        assert alias not in self._aliases
        assert len(self._aliases) < 2
        self._aliases.append(alias)

    def unset_alias(self, alias):
        assert alias in self._aliases
        self._aliases.remove(alias)


@pytest.mark.parametrize(
    "name, aliases, expected",
    [
        ("Notepad12FX,0,0-out:capture_1", [], "capture_1"),
        ("Notepad12FX,0,0-out:othername", ["playback_2"], "playback_2"),
        ("Notepad12FX,0,0-out:capture_3", ["some alias", "playback_4"], "capture_3"),
        ("Notepad12FX,0,0-out:othername", [], None),
        ("system:capture_1", ["alsa_pcm:hw:Notepad12FX:out1"], "capture_1"),
        ("system:playback_2", ["alsa_pcm:hw:Notepad12FX:in2"], "playback_2"),
        (
            "system:othername",
            ["alsa_pcm:hw:Notepad12FX:out3", "capture_3"],
            "capture_3",
        ),
    ],
)
def test_port_constructor(name, aliases, expected):
    port_mock = MockJackPort(name, aliases)
    port = jacksync.Port(port_mock)
    assert port.originalname == expected


@pytest.mark.parametrize(
    "name, aliases, expected",
    [
        ("Notepad12FX,0,0-out:capture_1", [], True),
        ("Notepad12FX,0,0-out:othername", ["playback_2"], True),
        ("Notepad12FX,0,0-out:capture_3", ["some alias", "playback_4"], True),
        ("Notepad12FX,0,0-out:othername", [], True),
        ("system:capture_1", ["alsa_pcm:hw:Notepad12FX:out1"], True),
        ("system:playback_2", ["alsa_pcm:hw:Notepad12FX:in2"], True),
        ("system:othername", ["alsa_pcm:hw:Notepad12FX:out3", "capture_3"], True),
        ("system:capture_1", [], False),
        ("system:capture_1", ["alias1", "alias2"], False),
    ],
)
def test_port_is_notepad(name, aliases, expected):
    port_mock = MockJackPort(name, aliases)
    port = jacksync.Port(port_mock)
    assert port.is_notepad() == expected


@pytest.mark.parametrize(
    "name, aliases, new_name, expected_aliases",
    [
        ("Notepad12FX,0,0-out:alias", ["capture_1"], "alias", ["capture_1"]),
        ("Notepad12FX,0,0-out:capture_1", [], "alias", ["capture_1"]),
        ("Notepad12FX,0,0-out:capture_1", ["alias"], "alias", ["capture_1"]),
        ("Notepad12FX,0,0-out:alias", ["capture_1"], "new alias", ["capture_1"]),
        (
            "Notepad12FX,0,0-out:alias",
            ["removeme", "capture_1"],
            "alias",
            ["capture_1"],
        ),
        (
            "Notepad12FX,0,0-out:capture_1",
            ["removeme", "alias"],
            "alias",
            ["capture_1"],
        ),
        (
            "Notepad12FX,0,0-out:capture_1",
            ["removeme", "andme"],
            "alias",
            ["capture_1"],
        ),
        (
            "system:capture_1",
            ["alsa_pcm:hw:Notepad12FX:out1"],
            "alias",
            ["alsa_pcm:hw:Notepad12FX:out1", "capture_1"],
        ),
        (
            "system:playback_2",
            ["alsa_pcm:hw:Notepad12FX:in2", "removeme"],
            "alias",
            ["alsa_pcm:hw:Notepad12FX:in2", "playback_2"],
        ),
        (
            "system:alias",
            ["alsa_pcm:hw:Notepad12FX:out3", "capture_3"],
            "new alias",
            ["alsa_pcm:hw:Notepad12FX:out3", "capture_3"],
        ),
    ],
)
def test_port_rename(name, aliases, new_name, expected_aliases):
    port_mock = MockJackPort(name, aliases)
    port = jacksync.Port(port_mock)
    port.rename(new_name)
    assert port_mock.shortname == new_name
    assert port_mock.aliases == expected_aliases


def test_port_rename_none():
    port_mock = MockJackPort("Notepad12FX,0,0-out:alias", ["capture_1"])
    port = jacksync.Port(port_mock)
    port.rename(None)
    assert port_mock.shortname == "alias"
    assert port_mock.aliases == ["capture_1"]


@pytest.mark.parametrize(
    "name, aliases, expected",
    [
        ("Notepad12FX,0,0-out:capture_1", [], ["alias"]),
        ("Notepad12FX,0,0-out:capture_1", ["alias"], ["alias"]),
        ("Notepad12FX,0,0-out:capture_1", ["old1"], ["alias"]),
        ("Notepad12FX,0,0-out:capture_1", ["old1", "old2"], ["alias"]),
        ("Notepad12FX,0,0-out:alias", ["capture_1"], ["alias"]),
        ("Notepad12FX,0,0-out:alias", ["capture_1", "something"], ["alias"]),
        (
            "system:capture_1",
            ["alsa_pcm:hw:Notepad12FX:out1"],
            ["alsa_pcm:hw:Notepad12FX:out1", "alias"],
        ),
        (
            "system:capture_1",
            ["alsa_pcm:hw:Notepad12FX:out1", "alias"],
            ["alsa_pcm:hw:Notepad12FX:out1", "alias"],
        ),
        (
            "system:capture_1",
            ["alsa_pcm:hw:Notepad12FX:out1", "old alias"],
            ["alsa_pcm:hw:Notepad12FX:out1", "alias"],
        ),
        (
            "system:alias",
            ["alsa_pcm:hw:Notepad12FX:out1", "capture_1"],
            ["alsa_pcm:hw:Notepad12FX:out1", "alias"],
        ),
    ],
)
def test_port_alias(name, aliases, expected):
    port_mock = MockJackPort(name, aliases)
    port = jacksync.Port(port_mock)
    port.alias("alias")
    assert port_mock.shortname == "capture_1"
    assert port_mock.aliases == expected


@pytest.mark.parametrize(
    "name, aliases, expected",
    [
        ("Notepad12FX,0,0-out:capture_1", [], []),
        ("Notepad12FX,0,0-out:capture_1", ["alias"], []),
        ("Notepad12FX,0,0-out:capture_1", ["old1"], []),
        ("Notepad12FX,0,0-out:capture_1", ["old1", "old2"], []),
        ("Notepad12FX,0,0-out:alias", ["capture_1"], []),
        ("Notepad12FX,0,0-out:alias", ["capture_1", "something"], []),
        (
            "system:capture_1",
            ["alsa_pcm:hw:Notepad12FX:out1"],
            ["alsa_pcm:hw:Notepad12FX:out1"],
        ),
        (
            "system:capture_1",
            ["alsa_pcm:hw:Notepad12FX:out1", "alias"],
            ["alsa_pcm:hw:Notepad12FX:out1"],
        ),
        (
            "system:capture_1",
            ["alias", "alsa_pcm:hw:Notepad12FX:out1"],
            ["alsa_pcm:hw:Notepad12FX:out1"],
        ),
        (
            "system:alias",
            ["alsa_pcm:hw:Notepad12FX:out1", "capture_1"],
            ["alsa_pcm:hw:Notepad12FX:out1"],
        ),
        (
            "system:alias",
            ["capture_1", "alsa_pcm:hw:Notepad12FX:out1"],
            ["alsa_pcm:hw:Notepad12FX:out1"],
        ),
    ],
)
def test_port_reset(name, aliases, expected):
    port_mock = MockJackPort(name, aliases)
    port = jacksync.Port(port_mock)
    port.reset()
    assert port_mock.shortname == "capture_1"
    assert port_mock.aliases == expected


def test_port_reset_incomplete_port():
    port_mock = MockJackPort("system:somename", ["a", "b"])
    port = jacksync.Port(port_mock)
    port.reset()
    assert port_mock.shortname == "somename"
    assert port_mock.aliases == ["a", "b"]


@pytest.mark.parametrize(
    "name, aliases, expected",
    [
        ("Notepad12FX,0,0-out:capture_1", [], False),
        ("Notepad12FX,0,0-out:capture_1", ["alias"], True),
        ("Notepad12FX,0,0-out:capture_1", ["old1"], True),
        ("Notepad12FX,0,0-out:capture_1", ["old1", "old2"], True),
        ("Notepad12FX,0,0-out:alias", ["capture_1"], True),
        ("Notepad12FX,0,0-out:alias", ["capture_1", "something"], True),
    ],
)
def test_port_is_renamed(name, aliases, expected):
    port_mock = MockJackPort(name, aliases)
    port = jacksync.Port(port_mock)
    assert port.is_renamed() == expected


@pytest.mark.parametrize("found, routing", [(False, "INPUT_1_2"), (True, "UNKNOWN")])
def test_all_labels_invalid_dev(found, routing):
    notepad = MagicMock()
    notepad.found.return_value = found
    notepad.routingSource = routing
    assert jacksync.all_labels(notepad) == {}


def test_all_labels():
    notepad = MagicMock()
    notepad.found.return_value = True
    notepad.routingSource = "MASTER_L_R"
    notepad.fixedRouting = [
        (("capture_1", "capture_2"), ("c-1", "c-2")),
    ]
    notepad.playbackLabels = [
        (("playback_1", "playback_2"), ("p-1", "p-2")),
        (("playback_3", "playback_4"), ("p-3", "p-4")),
    ]
    notepad.routingTarget = ("capture_3", "capture_4")
    notepad.sources = {"MASTER_L_R": ("c-3", "c-4")}
    labels = jacksync.all_labels(notepad)
    for t in ("capture", "playback"):
        for n in (1, 2, 3, 4):
            assert labels[f"{t}_{n}"] == f"{t[0]}-{n}"


@pytest.fixture
def jack_client(mocker):
    client = mocker.patch("jack.Client").return_value
    client.__enter__.return_value = client
    return client


@pytest.fixture
def jacksync_port(mocker):
    return mocker.patch("soundcraft.jacksync.Port")


def test_notepad_ports(jack_client, jacksync_port):
    inputs = ["foo", "bar"]
    jack_client.get_ports.return_value = inputs
    jacksync_port.return_value.is_notepad.side_effect = [True, False]
    ports = list(jacksync.notepad_ports(jack_client))
    assert len(ports) == 1


class PortMocker:
    def __init__(self, client, port):
        self.client = client
        self.port = port

    def setup(self, n):
        self.client.get_ports.return_value = range(0, n)
        ports = [MagicMock() for i in range(0, n)]
        self.port.side_effect = ports
        return ports


@pytest.fixture
def port_mocker(jack_client, jacksync_port):
    return PortMocker(jack_client, jacksync_port)


def test_reset_all(port_mocker):
    ports = port_mocker.setup(2)
    jacksync.reset_all()
    for port in ports:
        port.reset.assert_called_once()


@pytest.mark.parametrize(
    "values, expected",
    [
        ([True, True, True], True),
        ([True, False, False], True),
        ([False, False, True], True),
        ([False, False, False], False),
    ],
)
def test_is_renamed(values, expected, port_mocker):
    ports = port_mocker.setup(len(values))
    for port, value in zip(ports, values):
        port.is_renamed.return_value = value
    assert jacksync.is_renamed() == expected


def test_ready_okay(jack_client):
    assert jacksync.ready()


def test_ready_false(mocker):
    mocker.patch("jack.Client").side_effect = Exception("failed")
    assert not jacksync.ready()
