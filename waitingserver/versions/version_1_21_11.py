from waitingserver.protocol import Protocol
from waitingserver.versions import Version_1_21_9


class Version_1_21_11(Version_1_21_9):
    protocol_version = 1073742109
    chunk_format = '1.21.11'

    hologram_entity_id = 131  # Text display
    map_entity_id = 60  # Glow item frame
    map_item_id = 1104  # Filled map


    def __init__(self, protocol: Protocol, bedrock: bool = False):
        super().__init__(protocol, bedrock)
