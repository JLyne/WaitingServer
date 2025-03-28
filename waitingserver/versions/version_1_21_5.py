from waitingserver.protocol import Protocol
from waitingserver.versions import Version_1_21_4


class Version_1_21_5(Version_1_21_4):
    protocol_version = 770
    chunk_format = '1.21.5'

    hologram_entity_id = 125  # Text display
    map_entity_id = 57  # Glow item frame
    map_item_id = 1042  # Filled map

    def __init__(self, protocol: Protocol, bedrock: False):
        super(Version_1_21_4, self).__init__(protocol, bedrock)
