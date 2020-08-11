import jack


class Port:
    def __init__(self, port):
        self.jack = port
        self.names = [self.jack.shortname] + self.jack.aliases
        self.originalname = None
        for name in self.names:
            # TODO: This works with ubuntu and the way it invokes zita-a2j
            # Is this universally useful?
            if name.startswith("capture_") or name.startswith("playback_"):
                self.originalname = name
                break

    def _rename(self, name, alias):
        if name is None:
            print(f"No target name supplied; Nothing to do")
            return
        if name in self.jack.aliases:
            print(f"Removing stale alias {name}")
            self.jack.unset_alias(name)
        if self.jack.shortname != name:
            print(f"Renaming {self.jack.shortname}->{name}")
            self.jack.shortname = name
        old_aliases = [a for a in self.jack.aliases if a != alias]
        for old_alias in old_aliases:
            print(f"Removing stale alias {old_alias}")
            self.jack.unset_alias(old_alias)
        if alias is None:
            print(f"No alias supplied")
            return
        if alias not in self.jack.aliases:
            print(f"Setting up alias {alias}")
            self.jack.set_alias(alias)

    def rename(self, alias):
        self._rename(alias, self.originalname)

    def alias(self, alias):
        self._rename(self.originalname, alias)

    def reset(self):
        self._rename(self.originalname, None)

    def is_renamed(self):
        return self.jack.shortname != self.originalname or len(self.jack.aliases) > 0


def all_labels(dev):
    if not dev.found() or dev.routingSource == "UNKNOWN":
        return {}
    labels = {}
    for targets, sources in dev.fixedRouting:
        for i in (0, 1):
            labels[targets[i]] = sources[i]
    for targets, sources in dev.playbackLabels:
        for i in (0, 1):
            labels[targets[i]] = sources[i]
    targets = dev.routingTarget
    sources = dev.sources[dev.routingSource]
    for i in (0, 1):
        labels[targets[i]] = sources[i]
    return labels


def jack_client():
    client = jack.Client("soundcraft-utils", no_start_server=True)
    return client


def notepad_ports(client):
    # TODO: This works with ubuntu and the way it invokes zita-a2j
    # Is this universally useful?
    return (Port(x) for x in client.get_ports("Notepad.*"))


def rename_all(dev, do_rename=True):
    with jack_client() as client:
        labels = all_labels(dev)
        for port in notepad_ports(client):
            if port.originalname not in labels:
                print(f"No label found for port {port.originalname}")
                next
            alias = labels[port.originalname]
            if do_rename:
                port.rename(alias)
            else:
                port.alias(alias)


def reset_all():
    with jack_client() as client:
        for port in notepad_ports(client):
            port.reset()


def is_renamed():
    with jack_client() as client:
        return any(p.is_renamed() for p in notepad_ports(client))


def ready():
    try:
        with jack_client():
            return True
    except Exception:
        return False
