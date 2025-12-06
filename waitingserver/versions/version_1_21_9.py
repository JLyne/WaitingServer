from typing import List

from quarry.types.uuid import UUID

from waitingserver.direction import Direction
from waitingserver.protocol import Protocol
from waitingserver.versions import Version_1_21_7


class Version_1_21_9(Version_1_21_7):
    protocol_version = 773
    chunk_format = '1.21.9'

    hologram_entity_id = 128  # Text display
    map_entity_id = 59  # Glow item frame
    map_item_id = 1104  # Filled map


    def __init__(self, protocol: Protocol, bedrock: bool = False):
        super().__init__(protocol, bedrock)

    def send_spawn(self, effects=False):
        spawn = self.current_world.spawn

        self.protocol.send_packet("set_chunk_cache_center",
                                  self.protocol.buff_type.pack_varint(0) + self.protocol.buff_type.pack_varint(0))

        self.protocol.send_packet("set_chunk_cache_radius",
                                  self.protocol.buff_type.pack_varint(10))

        self.protocol.send_packet("set_default_spawn_position",
                             self.protocol.buff_type.pack_global_position("minecraft:overworld",
                                                                 int(spawn.get('x')), int(spawn.get('y')),
                                                                 int(spawn.get('z'))) # Now global position
                             + self.protocol.buff_type.pack('ff', spawn.get('yaw'), spawn.get('pitch'))) # Added pitch

        self.protocol.send_packet("player_position",
                                  self.protocol.buff_type.pack_varint(0),
                                  self.protocol.buff_type.pack("ddddddffi",
                                                               spawn.get('x') + 0.5, spawn.get('y'), spawn.get('z') + 0.5,
                                                               0, 0, 0,
                                                               spawn.get('yaw'), spawn.get('pitch'),
                                                               0))

        if effects is True:
            self.send_spawn_effect()

        self.protocol.send_packet("game_event", self.protocol.buff_type.pack("Bf", 13, 0.0))

    def send_map_frame(self, pos: List[float], direction: Direction, map_id: int):
        self.protocol.send_packet("add_entity",
                                  self.protocol.buff_type.pack_varint(self.last_entity_id),
                                  self.protocol.buff_type.pack_uuid(UUID.random()),
                                  self.protocol.buff_type.pack_varint(self.map_entity_id),
                                  self.protocol.buff_type.pack("ddd", pos[0], pos[1], pos[2]),
                                  self.protocol.buff_type.pack_lpvec3(0, 0, 0), # Added movement vector
                                  self.protocol.buff_type.pack("bbb", 0, 0, 0),
                                  self.protocol.buff_type.pack_varint(int(direction))) # Removed movement shorts

        self.send_entity_metadata(self.last_entity_id, self.get_map_frame_metadata(map_id))
        self.last_entity_id += 1

    def send_status_hologram(self, pos: List[float]):
        entity_id = self.last_entity_id
        self.protocol.send_packet("add_entity",
                                  self.protocol.buff_type.pack_varint(self.last_entity_id),
                                  self.protocol.buff_type.pack_uuid(UUID.random()),
                                  self.protocol.buff_type.pack_varint(self.hologram_entity_id),
                                  self.protocol.buff_type.pack("ddd", pos[0], pos[1], pos[2]),
                                  self.protocol.buff_type.pack_lpvec3(0, 0, 0), # Added movement vector
                                  self.protocol.buff_type.pack("bbb", 0, 0, 0),
                                  self.protocol.buff_type.pack_varint(0)) # Removed movement shorts

        self.send_entity_metadata(entity_id, self.get_status_hologram_metadata())

        self.last_entity_id += 1
        return entity_id