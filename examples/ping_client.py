

import attr
import click
from twisted.internet import reactor, defer

from sphinxmixcrypto import SphinxParams, IMixPKI, IReader
from txmix import OnionTransportFactory
from txmix import MixClient, RandomRouteFactory, IMixTransport, IRouteFactory
from txmix import DummyPKI, RandReader


@attr.s
class PingClient(object):

    params = attr.ib(validator=attr.validators.instance_of(SphinxParams))
    pki = attr.ib(validator=attr.validators.provides(IMixPKI))
    client_id = attr.ib(validator=attr.validators.instance_of(bytes))
    rand_reader = attr.ib(validator=attr.validators.provides(IReader))
    transport = attr.ib(validator=attr.validators.provides(IMixTransport))
    route_factory = attr.ib(validator=attr.validators.provides(IRouteFactory))

    reply = ""
    reply_d = None

    def message_received(self, message):
        print "DEBUG: PingClient: message_received: %s" % message
        self.reply = message
        self.reply_d.callback(message)

    def start(self):
        self.client = MixClient(self.params,
                                self.pki,
                                self.client_id,
                                self.rand_reader,
                                self.transport,
                                self.message_received,
                                self.route_factory)
        d = self.client.start()
        return d

    def wait_for_reply(self):
        return self.reply_d

    def send(self, destination, message):
        """
        proxy to the MixClient's send method.
        returns a deferred
        """
        return self.client.send(destination, message)


@click.command()
@click.option('--tor-control-unix-socket', default=None, type=str, help="unix socket name for connecting to the tor control port")
@click.option('--tor-control-tcp-host', default=None, type=str, help="tcp host for connecting to the tor control port")
@click.option('--tor-data', default=None, type=str, help="launch tor data directory")
@defer.inlineCallbacks
def main(tor_control_unix_socket, tor_control_tcp_host, tor_data):
    params = SphinxParams(max_hops=5, payload_size=1024)
    pki = DummyPKI()
    client_id = b"client"
    rand_reader = RandReader()
    transport_factory = OnionTransportFactory(reactor, params, tor_control_unix_socket)
    transport = transport_factory.buildTransport()
    route_factory = RandomRouteFactory(params, pki, rand_reader)
    destination = pki.identities()[0]  # XXX todo: pick a more interesting destination
    message = b"ping"
    client = PingClient(params, pki, client_id, rand_reader, transport, route_factory)
    yield client.start()
    yield client.send(destination, message)
    yield client.wait_for_reply()
    defer.returnValue(None)


if __name__ == '__main__':
    try:
        reactor.callWhenRunning(main)
    except ClickException, e:
        e.show()
        sys.exit(1)
    reactor.run()
