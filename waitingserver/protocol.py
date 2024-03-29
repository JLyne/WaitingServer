import hmac
import json
import random
from copy import deepcopy

from quarry.net.server import ServerProtocol
from quarry.types import chat
from quarry.types.uuid import UUID

from waitingserver.log import file_handler, console_handler, logger
from waitingserver.prometheus import set_players_online

worlds = list()

versions = {}


class Protocol(ServerProtocol):
    bungee_forwarding = False
    velocity_forwarding = False
    velocity_forwarding_secret = None

    voting_mode = False
    voting_secret = None
    status_secret = None

    debug_mode = False

    def __init__(self, factory, remote_addr):
        super(Protocol, self).__init__(factory, remote_addr)

        self.velocity_message_id = None
        self.is_bedrock = False
        self.version = None

        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)

    def packet_handshake(self, buff):
        buff2 = deepcopy(buff)
        super().packet_handshake(buff)

        buff2.unpack_varint()
        p_connect_host = buff2.unpack_string()

        if self.bungee_forwarding is True:
            # Bungeecord ip forwarding, ip/uuid is included in host string separated by \00s
            split_host = str.split(p_connect_host, "\00")

            if len(split_host) < 3:
                logger.warning("Invalid bungeecord forwarding data received from {}".format(self.remote_addr))
                self.close("Invalid bungeecord forwarding data")
                return

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

            self.connect_host = host
            self.uuid = UUID.from_hex(online_uuid)

            logger.info("Bungeecord: {}".format(self.uuid))

        version = None

        # Select version handler
        for protocol_version, v in versions.items():
            if self.protocol_version >= protocol_version:
                version = v

        if version is not None:
            self.version = version(self, self.is_bedrock)
        else:
            self.close("Unsupported Minecraft Version")

    def packet_login_start(self, buff):
        if self.login_expecting != 0:
            logger.warning("Unexpected login_start received from {}".format(self.remote_addr))
            self.close("Out-of-order login")
            return

        if self.velocity_forwarding is True:
            self.login_expecting = 2
            self.velocity_message_id = random.randint(0, 2147483647)
            self.send_packet("login_plugin_request",
                             self.buff_type.pack_varint(self.velocity_message_id),
                             self.buff_type.pack_string("velocity:player_info"),
                             b'')
            buff.read()
            return

        super().packet_login_start(buff)

    def packet_login_plugin_response(self, buff):
        if self.login_expecting != 2 or self.protocol_mode != "login":
            logger.warning("Unexpected login_plugin_response received from {}".format(self.remote_addr))
            self.close("Out-of-order login")
            return

        message_id = buff.unpack_varint()
        successful = buff.unpack('b')

        if message_id != self.velocity_message_id:
            logger.warning("Unexpected login_plugin_response received from {}".format(self.remote_addr))
            self.close("Unexpected login_plugin_response")
            return

        if not successful or len(buff) == 0:
            logger.warning("Empty velocity forwarding response received from {}".format(self.remote_addr))
            self.close("Empty velocity forwarding response")
            return

        # Verify HMAC
        signature = buff.read(32)
        verify = hmac.new(key=str.encode(self.velocity_forwarding_secret), msg=deepcopy(buff).read(),
                          digestmod="sha256").digest()

        if verify != signature:
            logger.warning("Invalid velocity forwarding response received from {}".format(self.remote_addr))
            self.close("Invalid velocity forwarding response received")
            buff.discard()
            return

        version = buff.unpack_varint()

        if version != 1:
            logger.warning("Unsupported velocity forwarding version received from {}".format(self.remote_addr))
            self.close("Unsupported velocity forwarding version")
            buff.discard()
            return

        buff.unpack_string()  # Ip

        self.uuid = buff.unpack_uuid()
        self.display_name = buff.unpack_string()

        buff.discard()  # Don't care about the rest

        self.login_expecting = None
        self.display_name_confirmed = True
        self.send_login_success()
        logger.info("Velocity: {} {}".format(self.display_name, self.uuid))

        if self.protocol_version < 764:
            self.player_joined()

    # 1.20.2+ send dimension codec during configuration phase
    def packet_login_acknowledged(self, buff):
        dimension_codec = self.version.get_dimension_codec()

        if dimension_codec is None:
            super().packet_login_acknowledged(buff)
            return

        self.switch_protocol_mode("configuration")
        self.send_packet("registry_data", self.buff_type.pack_nbt(dimension_codec))  # Required to get past Joining World screen
        self.send_packet("finish_configuration")  # Tell client to leave configuration mode

        buff.discard()

    def player_joined(self):
        if self.uuid is None:
            self.uuid = UUID.from_offline_player(self.display_name)

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

    # 1.19+
    def packet_chat_command(self, buff):
        self.version.packet_chat_command(buff)

    def packet_plugin_message(self, buff):
        channel = buff.unpack_string()
        data = buff.read()

        if channel != "serverstatus:status":
            return

        if self.status_secret is None:
            self.logger.warn("Ignoring status plugin message as no status secret is configured")
            return

        payload = json.loads(data.decode(encoding="utf-8"))
        payload_hmac = payload.get("hmac")

        msg = payload.get("servers", "{}")
        calculated_hmac = hmac.new(key=str.encode(self.status_secret, encoding="utf-8"),
                                   msg=str.encode(msg, encoding="utf-8"), digestmod="sha512")

        if calculated_hmac.hexdigest() != payload_hmac:
            self.logger.warn("Failed to validate status plugin message. Is the status secret configured correctly?")
            return

        server_statuses = json.loads(msg)
        self.factory.server_statuses = {}

        for server, status in server_statuses.items():
            separate_lines = status.get("separateLines", None)
            combined_lines = status.get("combinedLines", None)

            self.factory.server_statuses[server] = {
                'combined': chat.Message(json.loads(combined_lines)),
                'separate': None
            }

            if separate_lines is not None and len(separate_lines) == 2:
                self.factory.server_statuses[server]['separate'] = [
                    chat.Message(json.loads(separate_lines[0])), chat.Message(json.loads(separate_lines[1]))]

        for player in self.factory.players:
            if player.protocol_mode == "play":
                player.version.send_status_hologram_texts()


# Build dictionary of protocol version -> version class
# Local import to prevent circular import issues
def build_versions():
    import waitingserver.versions

    for version in vars(waitingserver.versions).values():
        if hasattr(version, 'protocol_version') and version.protocol_version is not None:
            versions[version.protocol_version] = version
