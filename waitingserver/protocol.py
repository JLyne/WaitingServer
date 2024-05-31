import hmac
import json
from copy import deepcopy

from quarry.net.server import ServerProtocol
from quarry.types import chat
from quarry.types.uuid import UUID

from waitingserver.log import file_handler, console_handler, logger
from waitingserver.prometheus import set_players_online

worlds = list()

versions = {}


class Protocol(ServerProtocol):
    voting_mode = False
    voting_secret = None
    status_secret = None

    debug_mode = False

    def __init__(self, factory, remote_addr):
        super(Protocol, self).__init__(factory, remote_addr)

        self.is_bedrock = False
        self.version = None

        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)

    def packet_handshake(self, buff):
        buff2 = deepcopy(buff)
        super().packet_handshake(buff)

        buff2.unpack_varint()
        p_connect_host = buff2.unpack_string()

        # Floodgate
        split_host = str.split(p_connect_host, "\00")

        if len(split_host) >= 2:
            # TODO: Should probably verify the encrypted data in some way.
            # Not important until something on this server uses uuids
            if split_host[1].startswith('^Floodgate^'):
                self.is_bedrock = True

                if self.factory.bungeecord_forwarding:
                    self.connect_host = split_host[2]
                    self.uuid = split_host[3]

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
            combined_lines = status.get("combinedLines", None)
            self.factory.server_statuses[server] = chat.Message(json.loads(combined_lines))

        for player in self.factory.players:
            if player.protocol_mode == "play":
                player.version.send_status_hologram_texts()

    def configuration(self):
        self.data_packs.add_data_pack(self.version.get_data_pack())
        self.complete_configuration()

# Build dictionary of protocol version -> version class
# Local import to prevent circular import issues
def build_versions():
    import waitingserver.versions

    for version in vars(waitingserver.versions).values():
        if hasattr(version, 'protocol_version') and version.protocol_version is not None:
            versions[version.protocol_version] = version
