from typing import Dict, Tuple, Union, Protocol

from quarry.types import chat

from waitingserver.versions import Version_1_19_3


class Version_1_19_4(Version_1_19_3):
    protocol_version = 762
    chunk_format = '1.19.4'
    tag_format = '1.19.4'

    hologram_entity_id = 100 # Text display
    hologram_y_offset = -.6 # Text display is vertically aligned to the bottom, so move it down a bit to center a typical line count
    map_entity_id = 43 # Glow item frame
    map_item_id = 937 # Filled map

    def __init__(self, protocol: Protocol, bedrock: False):
        super(Version_1_19_4, self).__init__(protocol, bedrock)

        self.hologram_lines_separate = False # Text display handles newlines, so only need one entity

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

    @staticmethod
    def get_status_hologram_metadata(text: chat.Message = "") -> Dict[Tuple[int, int], Union[str, int, bool]]:
        return {
            (5, 22): text,  # Text (index 22, type 6 (chat))
            (1, 23): 150, # Max width
            (0, 14): 3,
        }
