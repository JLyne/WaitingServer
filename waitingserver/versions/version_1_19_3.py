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

    # FIXME: Remove everything below when quarry updates
    def send_entity_metadata(self, entity_id: int, metadata: Dict[Tuple[int, int], Union[str, int, bool]]):
        self.protocol.send_packet("entity_metadata",
                                  self.protocol.buff_type.pack_varint(entity_id),
                                  self.pack_entity_metadata(metadata))

    def pack_entity_metadata(self, metadata):
        """
        Packs entity metadata.
        """

        pack_position = lambda pos: self.protocol.buff_type.pack_position(*pos)
        pack_global_position = lambda pos: self.pack_global_position(*pos)

        out = b""
        for ty_key, val in metadata.items():
            ty, key = ty_key
            out += self.protocol.buff_type.pack('B', key)
            out += self.protocol.buff_type.pack_varint(ty)

            if   ty == 0:  out += self.protocol.buff_type.pack('b', val)
            elif ty == 1:  out += self.protocol.buff_type.pack_varint(val)
            elif ty == 2:  out += self.protocol.buff_type.pack('q', val)
            elif ty == 3:  out += self.protocol.buff_type.pack('f', val)
            elif ty == 4:  out += self.protocol.buff_type.pack_string(val)
            elif ty == 5:  out += self.protocol.buff_type.pack_chat(val)
            elif ty == 6:  out += self.protocol.buff_type.pack_optional(self.protocol.buff_type.pack_chat, val)
            elif ty == 7:  out += self.protocol.buff_type.pack_slot(**val)
            elif ty == 8:  out += self.protocol.buff_type.pack('?', val)
            elif ty == 9:  out += self.protocol.buff_type.pack_rotation(*val)
            elif ty == 10:  out += self.protocol.buff_type.pack_position(*val)
            elif ty == 11: out += self.protocol.buff_type.pack_optional(pack_position, val)
            elif ty == 12: out += self.protocol.buff_type.pack_direction(val)
            elif ty == 13: out += self.protocol.buff_type.pack_optional(self.protocol.buff_type.pack_uuid, val)
            elif ty == 14: out += self.protocol.buff_type.pack_block(val)
            elif ty == 15: out += self.protocol.buff_type.pack_nbt(val)
            elif ty == 16: out += self.protocol.buff_type.pack_particle(*val)
            elif ty == 17: out += self.protocol.buff_type.pack_villager(*val)
            elif ty == 18: out += self.protocol.buff_type.pack_optional_varint(val)
            elif ty == 19: out += self.protocol.buff_type.pack_pose(val)
            elif ty == 20:  out += self.protocol.buff_type.pack_varint(val)
            elif ty == 21:  out += self.protocol.buff_type.pack_varint(val)
            elif ty == 22:  out += self.protocol.buff_type.pack_optional(pack_global_position, val)
            elif ty == 23:  out += self.protocol.buff_type.pack_varint(val)
            else: raise ValueError("Unknown entity metadata type: %d" % ty)
        out += self.protocol.buff_type.pack('B', 255)
        return out

    def pack_global_position(self, dimension, x, y, z):
        """
        Packs a global position.
        """

        return self.protocol.buff_type.pack_string(dimension) + self.protocol.buff_type.pack_position(x, y, z)
    # FIXME: Remove everything above when quarry updates
