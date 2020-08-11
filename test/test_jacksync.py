from unittest.mock import MagicMock, call

import pytest

from soundcraft import jacksync


class MockJackPort:
    def __init__(self, shortname, aliases):
        self._shortname = shortname
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
    "shortname, aliases, expected",
    [
        ("capture_1", [], "capture_1"),
        ("othername", ["playback_2"], "playback_2"),
        ("capture_3", ["some alias", "playback_4"], "capture_3"),
        ("othername", [], None),
    ],
)
def test_port_constructor(shortname, aliases, expected):
    port_mock = MockJackPort(shortname, aliases)
    port = jacksync.Port(port_mock)
    assert port.originalname == expected


@pytest.mark.parametrize(
    "name, aliases, new_name, expected_aliases",
    [
        ("alias", ["capture_1"], "alias", ["capture_1"]),
        ("capture_1", [], "alias", ["capture_1"]),
        ("capture_1", ["alias"], "alias", ["capture_1"]),
        ("alias", ["capture_1"], "new alias", ["capture_1"]),
        ("alias", ["removeme", "capture_1"], "alias", ["capture_1"]),
        ("capture_1", ["removeme", "alias"], "alias", ["capture_1"]),
        ("capture_1", ["removeme", "andme"], "alias", ["capture_1"]),
    ],
)
def test_port_rename(name, aliases, new_name, expected_aliases):
    port_mock = MockJackPort(name, aliases)
    port = jacksync.Port(port_mock)
    port.rename(new_name)
    assert port_mock.shortname == new_name
    assert port_mock.aliases == expected_aliases


def test_port_rename_none():
    port_mock = MockJackPort("alias", ["capture_1"])
    port = jacksync.Port(port_mock)
    port.rename(None)
    assert port_mock.shortname == "alias"
    assert port_mock.aliases == ["capture_1"]


@pytest.mark.parametrize(
    "name, aliases",
    [
        ("capture_1", []),
        ("capture_1", ["alias"]),
        ("capture_1", ["old1"]),
        ("capture_1", ["old1", "old2"]),
        ("alias", ["capture_1"]),
        ("alias", ["capture_1", "something"]),
    ],
)
def test_port_alias(name, aliases):
    port_mock = MockJackPort(name, aliases)
    port = jacksync.Port(port_mock)
    port.alias("alias")
    assert port_mock.shortname == "capture_1"
    assert port_mock.aliases == ["alias"]


@pytest.mark.parametrize(
    "name, aliases",
    [
        ("capture_1", []),
        ("capture_1", ["alias"]),
        ("capture_1", ["old1"]),
        ("capture_1", ["old1", "old2"]),
        ("alias", ["capture_1"]),
        ("alias", ["capture_1", "something"]),
    ],
)
def test_port_reset(name, aliases):
    port_mock = MockJackPort(name, aliases)
    port = jacksync.Port(port_mock)
    port.reset()
    assert port_mock.shortname == "capture_1"
    assert port_mock.aliases == []


def test_port_reset_incomplete_port():
    port_mock = MockJackPort("somename", ["a", "b"])
    port = jacksync.Port(port_mock)
    port.reset()
    assert port_mock.shortname == "somename"
    assert port_mock.aliases == ["a", "b"]


@pytest.mark.parametrize(
    "name, aliases, expected",
    [
        ("capture_1", [], False),
        ("capture_1", ["alias"], True),
        ("capture_1", ["old1"], True),
        ("capture_1", ["old1", "old2"], True),
        ("alias", ["capture_1"], True),
        ("alias", ["capture_1", "something"], True),
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
    ports = list(jacksync.notepad_ports(jack_client))
    assert len(ports) == len(inputs)
    jacksync_port.assert_has_calls([call(x) for x in inputs])


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
