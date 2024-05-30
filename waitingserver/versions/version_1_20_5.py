from typing import Dict, Tuple, Union

from quarry.types.namespaced_key import NamespacedKey

from waitingserver.protocol import Protocol
from waitingserver.versions import Version_1_20_3


class Version_1_20_5(Version_1_20_3):
    protocol_version = 766
    chunk_format = '1.20.5'
    tag_format = '1.20.5'

    hologram_entity_id = 105  # Text display
    map_entity_id = 47  # Glow item frame
    map_item_id = 982  # Filled map

    def __init__(self, protocol: Protocol, bedrock: False):
        super(Version_1_20_5, self).__init__(protocol, bedrock)

    def send_join_game(self):
        dimension_registry = self.protocol.data_packs.get_registry(NamespacedKey.minecraft('dimension_type'))
        dimension = dimension_registry.get(self.current_world.dimension)

        self.protocol.send_packet("join_game",
                                  self.protocol.buff_type.pack("i?", 0, False),
                                  self.protocol.buff_type.pack_varint(2),
                                  self.protocol.buff_type.pack_string("rtgame:waiting"),
                                  self.protocol.buff_type.pack_string("rtgame:reset"),
                                  self.protocol.buff_type.pack_varint(0),
                                  self.protocol.buff_type.pack_varint(7),
                                  self.protocol.buff_type.pack_varint(0),
                                  self.protocol.buff_type.pack("???", False, True, False),
                                  self.protocol.buff_type.pack_varint(dimension['id']),  # Now varint
                                  self.protocol.buff_type.pack_string("rtgame:waiting"),
                                  self.protocol.buff_type.pack("qBb??", 0, 1, 1, False, False),
                                  self.protocol.buff_type.pack("?", False),
                                  self.protocol.buff_type.pack_varint(0),
                                  self.protocol.buff_type.pack("?", False))  # Disable secure chat

    def send_respawn(self):
        dimension_registry = self.protocol.data_packs.get_registry(NamespacedKey.minecraft('dimension_type'))
        dimension = dimension_registry.get(self.current_world.dimension)
        print(self.current_world.name)
        print(self.current_world.dimension)

        self.protocol.send_packet("respawn",
                                  self.protocol.buff_type.pack_varint(dimension['id']), # Now varint
                                  self.protocol.buff_type.pack_string("rtgame:reset"),
                                  self.protocol.buff_type.pack("qBB", 0, 1, 1),
                                  self.protocol.buff_type.pack("???", False, False, False),
                                  self.protocol.buff_type.pack_varint(0),
                                  self.protocol.buff_type.pack("b", 0))

        self.protocol.send_packet("respawn",
                                  self.protocol.buff_type.pack_varint(dimension['id']), # Now varint
                                  self.protocol.buff_type.pack_string("rtgame:waiting"),
                                  self.protocol.buff_type.pack("qBB", 0, 1, 1),
                                  self.protocol.buff_type.pack("???", False, False, False),
                                  self.protocol.buff_type.pack_varint(0),
                                  self.protocol.buff_type.pack("b", 0))

    def get_map_frame_metadata(self, map_id: int) -> Dict[Tuple[int, int], Union[str, int, bool]]:
        return {
            (0, 0): 0x20,  # Invisible (index 0, type 0 (byte))
            (7, 8): {'item': self.map_item_id, 'count': 1, 'structured_data': {
                'map_id': map_id
            }},  # Item (type 7 (slot), index 8)
        }
