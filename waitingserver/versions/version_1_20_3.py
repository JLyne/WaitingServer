from typing import Protocol

from waitingserver.versions import Version_1_20_2


class Version_1_20_3(Version_1_20_2):
    protocol_version = 765
    chunk_format = '1.20.3'
    tag_format = '1.20.3'

    hologram_entity_id = 101  # Text display
    map_entity_id = 44  # Glow item frame
    map_item_id = 979  # Filled map

    def __init__(self, protocol: Protocol, bedrock: False):
        super(Version_1_20_2, self).__init__(protocol, bedrock)

    def send_spawn(self, effects=False):
        super().send_spawn(effects)
        self.protocol.send_packet("change_game_state", self.protocol.buff_type.pack("Bf", 13, 0.0))


