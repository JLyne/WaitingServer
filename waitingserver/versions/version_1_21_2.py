from quarry.types.namespaced_key import NamespacedKey

from waitingserver.protocol import Protocol
from waitingserver.versions import Version_1_21


class Version_1_21_2(Version_1_21):
    protocol_version = 768
    chunk_format = '1.21.2'

    hologram_entity_id = 125  # Text display
    map_entity_id = 58  # Glow item frame
    map_item_id = 1022  # Filled map

    def __init__(self, protocol: Protocol, bedrock: False):
        super(Version_1_21, self).__init__(protocol, bedrock)

    def send_join_game(self):
        dimension_registry = self.protocol.data_packs.get_registry(NamespacedKey.minecraft('dimension_type'))
        id = list(dimension_registry).index(self.current_world.dimension)

        self.protocol.send_packet("login",
                                  self.protocol.buff_type.pack("i?", 0, False),
                                  self.protocol.buff_type.pack_varint(2),
                                  self.protocol.buff_type.pack_string("rtgame:waiting"),
                                  self.protocol.buff_type.pack_string("rtgame:reset"),
                                  self.protocol.buff_type.pack_varint(0),
                                  self.protocol.buff_type.pack_varint(7),
                                  self.protocol.buff_type.pack_varint(0),
                                  self.protocol.buff_type.pack("???", False, True, False),
                                  self.protocol.buff_type.pack_varint(id),
                                  self.protocol.buff_type.pack_string("rtgame:waiting"),
                                  self.protocol.buff_type.pack("qBb??", 0, 1, 1, False, False),
                                  self.protocol.buff_type.pack("?", False),
                                  self.protocol.buff_type.pack_varint(0),
                                  self.protocol.buff_type.pack_varint(64), # Sea level
                                  self.protocol.buff_type.pack("?", False))

    def send_spawn(self, effects=False):
        spawn = self.current_world.spawn

        self.protocol.send_packet("set_default_spawn_position",
                                  self.protocol.buff_type.pack("iii", int(spawn.get('x')), int(spawn.get('y')),
                                                               int(spawn.get('z'))))

        self.protocol.send_packet("player_position",
                                  self.protocol.buff_type.pack_varint(0), # Move to front
                                  self.protocol.buff_type.pack("ddddddffi",
                                                               spawn.get('x') + 0.5, spawn.get('y'), spawn.get('z') + 0.5,
                                                               0, 0, 0, # Add second vector for movement
                                                               spawn.get('yaw'), spawn.get('pitch'),
                                                               0)) # Bitset instead of boolean

        if effects is True:
            self.send_spawn_effect()

        self.protocol.send_packet("game_event", self.protocol.buff_type.pack("Bf", 13, 0.0))

    def send_time(self):
        # Time of day
        self.protocol.send_packet('set_time',
                                  self.protocol.buff_type.pack("Qq?", 0, self.current_world.time,
                                                               self.current_world.cycle)) # Boolean for fixed time instead of negative time value

    def send_respawn(self):
        dimension_registry = self.protocol.data_packs.get_registry(NamespacedKey.minecraft('dimension_type'))
        id = list(dimension_registry).index(self.current_world.dimension)

        self.protocol.send_packet("respawn",
                                  self.protocol.buff_type.pack_varint(id),
                                  self.protocol.buff_type.pack_string("rtgame:reset"),
                                  self.protocol.buff_type.pack("qBB", 0, 1, 1),
                                  self.protocol.buff_type.pack("???", False, False, False),
                                  self.protocol.buff_type.pack_varint(0),
                                  self.protocol.buff_type.pack("b", 0),
                                  self.protocol.buff_type.pack_varint(64)) # Sea Level

        self.protocol.send_packet("respawn",
                                  self.protocol.buff_type.pack_varint(id),
                                  self.protocol.buff_type.pack_string("rtgame:waiting"),
                                  self.protocol.buff_type.pack("qBB", 0, 1, 1),
                                  self.protocol.buff_type.pack("???", False, False, False),
                                  self.protocol.buff_type.pack_varint(0),
                                  self.protocol.buff_type.pack("b", 0),
                                  self.protocol.buff_type.pack_varint(64)) # Sea Level