from quarry.types.nbt import TagInt, TagRoot, TagCompound

from waitingserver.versions import Version_1_16_2


class Version_1_17(Version_1_16_2):
    protocol_version = 755
    chunk_format = '1.17'
    map_format = '1.17'

    map_item_id = 847

    def get_dimension_settings(self, name: str):
        settings = super().get_dimension_settings(name)

        settings['min_y'] = TagInt(0)
        settings['height'] = TagInt(256)

        return settings

    def send_spawn(self, effects=False):
        spawn = self.current_world.spawn

        self.protocol.send_packet("player_position_and_look",
                                  self.protocol.buff_type.pack("dddff?",
                                                               spawn.get('x') + 0.5, spawn.get('y'), spawn.get('z') + 0.5,
                                                               spawn.get('yaw'), spawn.get('pitch'), 0b00000),
                                  self.protocol.buff_type.pack_varint(0), self.protocol.buff_type.pack("?", True))

        if effects is True:
            self.send_spawn_effect()

    def send_reset_world(self):
        data = [
            self.protocol.buff_type.pack_nbt(TagRoot({'': TagCompound({})})),  # Heightmap
            self.protocol.buff_type.pack_varint(0),  # Data size
            self.protocol.buff_type.pack_varint(0),  # Block entity count
            self.protocol.buff_type.pack("?", True),  # Trust edges
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

