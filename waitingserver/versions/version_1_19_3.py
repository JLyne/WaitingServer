import json
from typing import Dict, Union, Tuple

from quarry.types import chat
from quarry.types.nbt import TagRoot, TagCompound, TagInt

from waitingserver.versions import Version_1_19_1


class Version_1_19_3(Version_1_19_1):
    protocol_version = 761
    chunk_format = '1.19.3'
    tag_format = '1.19.3'

    map_entity_id = 36 # Glow item frame
    map_item_id = 914 # Filled map

    def send_spawn(self, effects=False):
        spawn = self.current_world.spawn

        self.protocol.send_packet("spawn_position",
                                  self.protocol.buff_type.pack("iii", int(spawn.get('x')), int(spawn.get('y')),
                                                               int(spawn.get('z'))))
        super().send_spawn(effects)

    def send_tablist(self):
        self.protocol.send_packet("player_list_header_footer",
                                  self.protocol.buff_type.pack_string(json.dumps({
                                      "text": "\n\ue300\n"
                                  })),
                                  self.protocol.buff_type.pack_string(json.dumps({"translate": ""})))

        self.protocol.send_packet("player_list_item",
                                  self.protocol.buff_type.pack('B', 63),
                                  self.protocol.buff_type.pack_varint(1),
                                  self.protocol.buff_type.pack_uuid(self.protocol.uuid),
                                  self.protocol.buff_type.pack_string(self.protocol.display_name),
                                  self.protocol.buff_type.pack_varint(0),
                                  self.protocol.buff_type.pack("?", False),  # False for no chat session info
                                  self.protocol.buff_type.pack_varint(1),
                                  self.protocol.buff_type.pack("?", True),  # Show in tab list
                                  self.protocol.buff_type.pack_varint(1),
                                  self.protocol.buff_type.pack("?", False))

    def send_global_sound(self, sound: str, channel: int):
        spawn = self.current_world.spawn

        self.protocol.send_packet("sound_effect",
                                  self.protocol.buff_type.pack_varint(0),
                                  self.protocol.buff_type.pack_string(sound),
                                  self.protocol.buff_type.pack("?", False),
                                  self.protocol.buff_type.pack_varint(channel),
                                  self.protocol.buff_type.pack("iiiffq",
                                                               int(spawn.get('x')),
                                                               int(spawn.get('y')),
                                                               int(spawn.get('z')), 100000.0, 1, 0))  # Extra byte for seed

    @staticmethod
    def get_status_hologram_metadata(text: chat.Message = "") -> Dict[Tuple[int, int], Union[str, int, bool]]:
        return {
            (0, 0): 0x20,  # Custom name (index 0, type 0 (byte))
            (8, 5): True,  # No gravity (index 5, type 8 (boolean))
            (6, 2): text,  # Custom name (index 2, type 6 (optional chat))
            (8, 3): True,  # Custom name visible (index 3, type 8 (boolean))
        }

    def get_map_frame_metadata(self, map_id: int) -> Dict[Tuple[int, int], Union[str, int, bool]]:
        map_nbt = TagRoot({
            '': TagCompound({
                'map': TagInt(map_id)
            })
        })

        return {
            (0, 0): 0x20,  # Invisible (index 0, type 0 (byte))
            (7, 8): {'item': self.map_item_id, 'count': 1, 'tag': map_nbt},  # Item (type 7 (slot), index 8)
        }
