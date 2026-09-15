from waitingserver.protocol import Protocol
from waitingserver.versions import Version_26_2


class Version_26_3(Version_26_2):
    protocol_version = 777
    chunk_format = '26.3'

    hologram_entity_id = 135  # Text display
    map_entity_id = 61  # Glow item frame
    map_item_id = 1238  # Filled map

    def __init__(self, protocol: Protocol, bedrock: bool = False):
        super().__init__(protocol, bedrock)
