from typing import Dict, Tuple, Union

from waitingserver.protocol import Protocol
from waitingserver.versions import Version_1_21_5


class Version_1_21_6(Version_1_21_5):
    protocol_version = 771
    chunk_format = '1.21.6'

    hologram_entity_id = 126  # Text display
    map_entity_id = 58  # Glow item frame
    map_item_id = 1059  # Filled map

    def __init__(self, protocol: Protocol, bedrock: bool = False):
        super().__init__(protocol, bedrock)

    def get_map_frame_metadata(self, map_id: int) -> Dict[Tuple[int, int], Union[str, int, bool]]:
        return {
            (0, 0): 0x20,  # Invisible (index 0, type 0 (byte))
            (7, 9): {'item': self.map_item_id, 'count': 1, 'structured_data': {
                'map_id': map_id
            }},  # Item (type 7 (slot), index 8)
        }
