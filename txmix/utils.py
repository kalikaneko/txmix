
import os
import attr
from zope.interface.declarations import implementer

from sphinxmixcrypto import IReader, IMixPKI, IKeyState, GroupCurve25519, SECURITY_PARAMETER


def is_16bytes(instance, attribute, value):
    """
    validator for node_id which should be a 16 byte value
    """
    if not isinstance(value, bytes) or len(value) != 16:
        raise ValueError("must be 16 byte value")


def is_32bytes(instance, attribute, value):
    """
    validator for node_id which should be a 32 byte value
    """
    if not isinstance(value, bytes) or len(value) != 32:
        raise ValueError("must be 32 byte value")


@implementer(IKeyState)
@attr.s
class MixKeyState(object):

    public_key = attr.ib(validator=is_32bytes)
    private_key = attr.ib(validator=is_32bytes)

    def get_private_key(self):
        return self.private_key

    def get_public_key(self):
        return self.public_key


@implementer(IMixPKI)
class DummyPKI(object):

    def __init__(self):
        self.node_map = {}
        self.addr_map = {}
        self.client_map = {}

    def set(self, node_id, pub_key, addr):
        assert node_id not in self.node_map.keys()
        self.node_map[node_id] = pub_key
        self.addr_map[node_id] = addr

    def get(self, node_id):
        return self.node_map[node_id]

    def identities(self):
        return self.node_map.keys()

    def set_client_addr(self, transport_name, client_id, addr):
        self.client_map[client_id] = addr

    def get_client_addr(self, transport_name, client_id):
        return self.client_map[client_id]

    def get_mix_addr(self, transport_name, node_id):
        return self.addr_map[node_id]

    def rotate(self, node_id, new_pub_key, signature):
        pass


def generate_node_keypair(rand_reader):
    group = GroupCurve25519()
    private_key = group.gensecret(rand_reader)
    public_key = group.expon(group.generator, private_key)
    return public_key, private_key


def generate_node_id(rand_reader):
    idnum = rand_reader.read(4)
    node_id = b"\xff" + idnum + (b"\x00" * (SECURITY_PARAMETER - len(idnum) - 1))
    return node_id


@implementer(IReader)
class EntropyReader:
    def __init__(self):
        pass

    def read(self, n):
        return os.urandom(n)
