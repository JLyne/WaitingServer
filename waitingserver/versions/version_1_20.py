from typing import Protocol

from quarry.types.nbt import TagRoot, TagCompound

from waitingserver.versions import Version_1_19_4


class Version_1_20(Version_1_19_4):
    protocol_version = 763
    chunk_format = '1.20'
    tag_format = '1.20'

    hologram_entity_id = 100 # Text display
    map_entity_id = 43 # Glow item frame
    map_item_id = 941 # Filled map

    def __init__(self, protocol: Protocol, bedrock: False):
        super(Version_1_19_4, self).__init__(protocol, bedrock)

        self.hologram_lines_separate = False # Text display handles newlines, so only need one entity

    def send_join_game(self):
        self.init_dimension_codec()

        self.protocol.send_packet("join_game",
                                  self.protocol.buff_type.pack("i?Bb", 0, False, 1, 1),
                                  self.protocol.buff_type.pack_varint(2),
                                  self.protocol.buff_type.pack_string("rtgame:waiting"),
                                  self.protocol.buff_type.pack_string("rtgame:reset"),
                                  self.protocol.buff_type.pack_nbt(self.dimension_codec),
                                  self.protocol.buff_type.pack_string(self.current_world.dimension),
                                  self.protocol.buff_type.pack_string("rtgame:waiting"),
                                  self.protocol.buff_type.pack("q", 0),
                                  self.protocol.buff_type.pack_varint(0),
                                  self.protocol.buff_type.pack_varint(7),
                                  self.protocol.buff_type.pack_varint(0),
                                  self.protocol.buff_type.pack("????", False, True, False, False),
                                  self.protocol.buff_type.pack("?", False),
                                  self.protocol.buff_type.pack_varint(0))  # Portal cooldown

    def send_reset_world(self):
        data = [
            self.protocol.buff_type.pack_nbt(TagRoot({'': TagCompound({})})),  # Heightmap
            self.protocol.buff_type.pack_varint(0),  # Data size
            self.protocol.buff_type.pack_varint(0),  # Block entity count
            self.protocol.buff_type.pack_varint(0),  # Sky light mask
            self.protocol.buff_type.pack_varint(0),  # Block light mask
            self.protocol.buff_type.pack_varint(0),  # Empty sky light mask
            self.protocol.buff_type.pack_varint(0),  # Empty block light mask
            self.protocol.buff_type.pack_varint(0),  # Sky light array count
            self.protocol.buff_type.pack_varint(0),  # Block light array count
        ]

        for x in range(-8, 8):
            for y in range(-8, 8):
                self.protocol.send_packet("chunk_data", self.protocol.buff_type.pack("ii", x, y), *data)

    def send_respawn(self):
        self.protocol.send_packet("respawn",
                                  self.protocol.buff_type.pack_string(self.current_world.dimension),  # Current dimension is now a string
                                  self.protocol.buff_type.pack_string("rtgame:reset"),
                                  self.protocol.buff_type.pack("qBB", 0, 1, 1),
                                  self.protocol.buff_type.pack("????", False, False, True, False),
                                  self.protocol.buff_type.pack_varint(0))

        self.protocol.send_packet("respawn",
                                  self.protocol.buff_type.pack_string(self.current_world.dimension),  # Current dimension is now a string
                                  self.protocol.buff_type.pack_string("rtgame:waiting"),
                                  self.protocol.buff_type.pack("qBB", 0, 1, 1),
                                  self.protocol.buff_type.pack("????", False, False, True, False),
                                  self.protocol.buff_type.pack_varint(0))
