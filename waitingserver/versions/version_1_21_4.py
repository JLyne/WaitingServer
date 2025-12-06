from waitingserver.protocol import Protocol
from waitingserver.versions import Version_1_21_2


class Version_1_21_4(Version_1_21_2):
    protocol_version = 769
    chunk_format = '1.21.4'

    hologram_entity_id = 124  # Text display
    map_entity_id = 57  # Glow item frame
    map_item_id = 1031  # Filled map

    def __init__(self, protocol: Protocol, bedrock: bool = False):
        super().__init__(protocol, bedrock)
