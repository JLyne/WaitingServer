import logging
import os
import sys

from argparse import ArgumentParser
from copy import deepcopy


from twisted.internet import reactor
from quarry.net.server import ServerFactory, ServerProtocol

from quarry.types.uuid import UUID

from waitingserver.prometheus import set_players_online, init_prometheus
from waitingserver.config import load_world_config

worlds = list()

if getattr(sys, 'frozen', False):  # PyInstaller adds this attribute
    # Running in a bundle
    path = os.path.join(sys._MEIPASS, 'waitingserver')
else:
    # Running in normal Python environment
    path = os.path.dirname(__file__)

# Logging
logger = logging.getLogger('waitingserver')
logger.setLevel(logging.DEBUG)

file_handler = logging.FileHandler(filename='waitingserver.log')
console_handler = logging.StreamHandler(sys.stderr)
formatter = logging.Formatter('[%(asctime)s %(levelname)s]: [%(name)s] %(message)s')
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)
logger.addHandler(console_handler)
logger.addHandler(file_handler)

versions = {}

class Protocol(ServerProtocol):
    def __init__(self, factory, remote_addr):
        self.uuid = UUID.from_offline_player('NotKatuen')

        self.forwarded_uuid = None
        self.forwarded_host = None
        self.is_bedrock = False
        self.version = None

        super(Protocol, self).__init__(factory, remote_addr)

        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)

    def packet_handshake(self, buff):
        buff2 = deepcopy(buff)
        super().packet_handshake(buff)

        buff2.unpack_varint()
        p_connect_host = buff2.unpack_string()

        # Bungeecord ip forwarding, ip/uuid is included in host string separated by \00s
        split_host = str.split(p_connect_host, "\00")

        if len(split_host) >= 3:
            # TODO: Should probably verify the encrypted data in some way.
            # Not important until something on this server uses uuids
            if split_host[1] == 'Geyser-Floodgate':
                self.is_bedrock = True

                host = split_host[4]
                online_uuid = split_host[5]
            elif split_host[1].startswith('^Floodgate^'):
                self.is_bedrock = True

                host = split_host[2]
                online_uuid = split_host[3]
            else:
                host = split_host[1]
                online_uuid = split_host[2]

            self.forwarded_host = host
            self.forwarded_uuid = UUID.from_hex(online_uuid)

        version = None

        # Select version handler
        for protocol_version, v in versions.items():
            if self.protocol_version >= protocol_version:
                version = v

        if version is not None:
            self.version = version(self, self.is_bedrock)
        else:
            self.close("Unsupported Minecraft Version")

    def player_joined(self):
        # Overwrite with forwarded information if present
        if self.forwarded_uuid is not None:
            self.uuid = self.forwarded_uuid
            self.display_name_confirmed = True

        if self.forwarded_host is not None:
            self.connect_host = self.forwarded_host

        super().player_joined()

        set_players_online(len(self.factory.players))

        self.version.player_joined()

    def player_left(self):
        super().player_left()

        set_players_online(len(self.factory.players))

    def packet_player_position(self, buff):
        self.version.packet_player_position(buff)

    def packet_player_position_and_look(self, buff):
        self.version.packet_player_position_and_look(buff)

    def packet_chat_message(self, buff):
        self.version.packet_chat_message(buff)


# Build dictionary of protocol version -> version class
# Local import to prevent circlular import issues
def build_versions():
    import waitingserver.versions

    for version in vars(waitingserver.versions).values():
        if hasattr(version, 'protocol_version') and version.protocol_version is not None:
            versions[version.protocol_version] = version


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-a", "--host", default="127.0.0.1", help="bind address")
    parser.add_argument("-p", "--port", default=25567, type=int, help="bind port")
    parser.add_argument("-m", "--max", default=65535, type=int, help="player count")
    parser.add_argument("-r", "--metrics", default=None, type=int, help="expose prometheus metrics on specified port")

    args = parser.parse_args()

    server_factory = ServerFactory()
    server_factory.protocol = Protocol
    server_factory.max_players = args.max
    server_factory.motd = "Waiting Server"
    server_factory.online_mode = False
    server_factory.compression_threshold = 1500

    metrics_port = args.metrics

    load_world_config()
    build_versions()

    if metrics_port is not None:
        init_prometheus(metrics_port)

    server_factory.listen(args.host, args.port)
    logger.info('Server started')
    logger.info("Listening on {}:{}".format(args.host, args.port))
    reactor.run()
