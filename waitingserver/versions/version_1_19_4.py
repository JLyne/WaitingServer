from waitingserver.versions import Version_1_19_3


class Version_1_19_4(Version_1_19_3):
    protocol_version = 1073741946
    chunk_format = '1.19.4'
    tag_format = '1.19.4'

    map_entity_id = 43 # Glow item frame
    map_item_id = 937 # Filled map

    def send_spawn(self, effects=False):
        spawn = self.current_world.spawn

        self.protocol.send_packet("spawn_position",
                                  self.protocol.buff_type.pack("iii", int(spawn.get('x')), int(spawn.get('y')),
                                                               int(spawn.get('z'))))

        self.protocol.send_packet("player_position_and_look",
                                  self.protocol.buff_type.pack("dddff?",
                                                               spawn.get('x') + 0.5, spawn.get('y'), spawn.get('z') + 0.5,
                                                               spawn.get('yaw'), spawn.get('pitch'), 0b00000),
                                  self.protocol.buff_type.pack_varint(0)) # Remove dismount vehicle

        if effects is True:
            self.send_spawn_effect()
