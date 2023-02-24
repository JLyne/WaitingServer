import json
from typing import List

from quarry.types.nbt import TagInt
from quarry.types.uuid import UUID

from waitingserver.versions import Version_1_18_2
from waitingserver.direction import Direction


class Version_1_19(Version_1_18_2):
    protocol_version = 759

    chunk_format = '1.19'
    tag_format = '1.19'

    armor_stand_id = 2
    item_frame_id = 35
    map_item_id = 886

    def send_join_game(self):
        self.init_dimension_codec()

        self.protocol.send_packet("join_game",
                                  self.protocol.buff_type.pack("i?Bb", 0, False, 1, 1),
                                  self.protocol.buff_type.pack_varint(2),
                                  self.protocol.buff_type.pack_string("rtgame:waiting"),
                                  self.protocol.buff_type.pack_string("rtgame:reset"),
                                  self.protocol.buff_type.pack_nbt(self.dimension_codec),
                                  self.protocol.buff_type.pack_string(self.current_world.dimension),  # Current dimension is now a string
                                  self.protocol.buff_type.pack_string("rtgame:waiting"),
                                  self.protocol.buff_type.pack("q", 0),
                                  self.protocol.buff_type.pack_varint(0),
                                  self.protocol.buff_type.pack_varint(7),
                                  self.protocol.buff_type.pack_varint(0),
                                  self.protocol.buff_type.pack("?????", False, True, False, False, False))  # Extra False for not providing a death location

    def send_respawn(self):
        self.protocol.send_packet("respawn",
                                  self.protocol.buff_type.pack_string(self.current_world.dimension),  # Current dimension is now a string
                                  self.protocol.buff_type.pack_string("rtgame:reset"),
                                  self.protocol.buff_type.pack("qBB", 0, 1, 1),
                                  self.protocol.buff_type.pack("????", False, False, True, False))

        self.protocol.send_packet("respawn",
                                  self.protocol.buff_type.pack_string(self.current_world.dimension),  # Current dimension is now a string
                                  self.protocol.buff_type.pack_string("rtgame:waiting"),
                                  self.protocol.buff_type.pack("qBB", 0, 1, 1),
                                  self.protocol.buff_type.pack("????", False, False, True, False))

    def get_dimension_settings(self, name: str):
        settings = super().get_dimension_settings(name)

        # New dimension settings
        settings['monster_spawn_block_light_limit'] = TagInt(0)
        settings['monster_spawn_light_level'] = TagInt(0)

        return settings

    def send_status_hologram(self, pos: List[float]):
        entity_id = self.last_entity_id
        self.protocol.send_packet("spawn_object",  # All entity spawns now use spawn_object
                                  self.protocol.buff_type.pack_varint(self.last_entity_id),
                                  self.protocol.buff_type.pack_uuid(UUID.random()),
                                  self.protocol.buff_type.pack_varint(self.armor_stand_id),
                                  self.protocol.buff_type.pack("dddbbbbhhh",
                                                               pos[0], pos[1], pos[2],
                                                               0, 0, 0, 0,  # Extra byte for head yaw
                                                               0, 0, 0))

        self.send_entity_metadata(entity_id, self.get_status_hologram_metadata())

        self.last_entity_id += 1
        return entity_id

    def send_map_frame(self, pos: List[float], direction: Direction, map_id: int):
        self.protocol.send_packet("spawn_object",
                                  self.protocol.buff_type.pack_varint(self.last_entity_id),
                                  self.protocol.buff_type.pack_uuid(UUID.random()),
                                  self.protocol.buff_type.pack_varint(self.item_frame_id),
                                  self.protocol.buff_type.pack("dddbbb", pos[0], pos[1], pos[2], 0, 0, 0),  # Extra byte for head yaw
                                  self.protocol.buff_type.pack_varint(int(direction)),
                                  self.protocol.buff_type.pack("hhh", 0, 0, 0))

        self.send_entity_metadata(self.last_entity_id, self.get_map_frame_metadata(map_id))
        self.last_entity_id += 1

    def send_global_sound(self, sound: str, channel: int):
        spawn = self.current_world.spawn

        self.protocol.send_packet("named_sound_effect",
                                  self.protocol.buff_type.pack_string(sound),
                                  self.protocol.buff_type.pack_varint(channel),
                                  self.protocol.buff_type.pack("iiiffq",
                                                               int(spawn.get('x')),
                                                               int(spawn.get('y')),
                                                               int(spawn.get('z')), 100000.0, 1, 0))  # Extra byte for seed

    def send_tablist(self):
        self.protocol.send_packet("player_list_header_footer",
                                  self.protocol.buff_type.pack_string(json.dumps({
                                      "text": "\n\ue300\n"
                                  })),
                                  self.protocol.buff_type.pack_string(json.dumps({"translate": ""})))

        self.protocol.send_packet("player_list_item",
                                  self.protocol.buff_type.pack_varint(0),
                                  self.protocol.buff_type.pack_varint(1),
                                  self.protocol.buff_type.pack_uuid(self.protocol.uuid),
                                  self.protocol.buff_type.pack_string(self.protocol.display_name),
                                  self.protocol.buff_type.pack_varint(0),
                                  self.protocol.buff_type.pack_varint(1),
                                  self.protocol.buff_type.pack_varint(1),
                                  self.protocol.buff_type.pack("??", False, False))  # Extra false for unsigned profile

    def send_chat_message(self, message):
        # Use system chat for all messages
        self.protocol.send_packet('system_message',
                                  self.protocol.buff_type.pack_string(message),
                                  self.protocol.buff_type.pack("b", 1))

