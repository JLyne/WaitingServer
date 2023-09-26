from typing import Protocol, Dict, Tuple, Union

from quarry.types import chat

from waitingserver.versions import Version_1_20


class Version_1_20_2(Version_1_20):
    protocol_version = 764
    chunk_format = '1.20.2'
    tag_format = '1.20.2'

    def __init__(self, protocol: Protocol, bedrock: False):
        super(Version_1_20, self).__init__(protocol, bedrock)

    def send_join_game(self):
        self.protocol.send_packet("join_game",
                                  self.protocol.buff_type.pack("i?", 0, False),
                                  self.protocol.buff_type.pack_varint(2),
                                  self.protocol.buff_type.pack_string("rtgame:waiting"),
                                  self.protocol.buff_type.pack_string("rtgame:reset"),
                                  self.protocol.buff_type.pack_varint(0),
                                  self.protocol.buff_type.pack_varint(7),
                                  self.protocol.buff_type.pack_varint(0),
                                  self.protocol.buff_type.pack("???", False, True, False),  # Added is limited crafting
                                  self.protocol.buff_type.pack_string(self.current_world.dimension),  # Moved current dimension
                                  self.protocol.buff_type.pack_string("rtgame:waiting"),  # Moved current world
                                  self.protocol.buff_type.pack("qBb??", 0, 1, 1, False, False),  # Moved hashed seed, current/prev gamemode
                                  self.protocol.buff_type.pack("?", False),
                                  self.protocol.buff_type.pack_varint(0))

    def send_respawn(self):
        self.protocol.send_packet("respawn",
                                  self.protocol.buff_type.pack_string(self.current_world.dimension),
                                  self.protocol.buff_type.pack_string("rtgame:reset"),
                                  self.protocol.buff_type.pack("qBB", 0, 1, 1),
                                  self.protocol.buff_type.pack("???", False, False, False),  # Moved data kept
                                  self.protocol.buff_type.pack_varint(0),
                                  self.protocol.buff_type.pack("b", 0))  # Moved data kept

        self.protocol.send_packet("respawn",
                                  self.protocol.buff_type.pack_string(self.current_world.dimension),
                                  self.protocol.buff_type.pack_string("rtgame:waiting"),
                                  self.protocol.buff_type.pack("qBB", 0, 1, 1),
                                  self.protocol.buff_type.pack("???", False, False, False),  # Moved data kept
                                  self.protocol.buff_type.pack_varint(0),
                                  self.protocol.buff_type.pack("b", 0))  # Moved data kept

    @staticmethod
    def get_status_hologram_metadata(text: chat.Message = "") -> Dict[Tuple[int, int], Union[str, int, bool]]:
        return {
            (5, 23): text,  # Text (index 23, type 6 (chat))
            (1, 24): 150,  # Max width
            (0, 15): 3,
        }