from quarry.types.chunk import PackedArray
from quarry.types.nbt import TagInt, TagLongArray, TagCompound, TagRoot

from waitingserver.versions import Version_1_16_2
from waitingserver.server import Protocol


class Version_1_17(Version_1_16_2):
    def __init__(self, protocol: Protocol, bedrock: False):
        super(Version_1_17, self).__init__(protocol, bedrock)
        self.version_name = '1.17'

    def get_dimension_settings(self):
        settings = super().get_dimension_settings()

        settings['min_y'] = TagInt(0)
        settings['height'] = TagInt(256)

        return settings

    def send_spawn(self, effects = False):
        spawn = self.current_world.spawn

        self.protocol.send_packet("player_position_and_look",
                                  self.protocol.buff_type.pack("dddff?",
                                                               spawn.get('x'), spawn.get('y'), spawn.get('z'),
                                                               spawn.get('yaw'), spawn.get('pitch'), 0b00000),
                                  self.protocol.buff_type.pack_varint(0), self.protocol.buff_type.pack("?", True))

        if effects is True:
            self.protocol.send_packet("effect",
                                      self.protocol.buff_type.pack("i", 2003),
                                      self.protocol.buff_type.pack_position(
                                          int(spawn.get('x')),
                                          int(spawn.get('y')),
                                          int(spawn.get('z'))),
                                      self.protocol.buff_type.pack("ib", 0, False))

    def send_reset_world(self):
        data = [
            self.protocol.buff_type.pack_varint(0),
            b'',
            self.protocol.buff_type.pack_nbt(
                TagRoot({'': TagCompound({"MOTION_BLOCKING": TagLongArray(PackedArray.empty_height())})})),
            self.protocol.buff_type.pack_varint(1024),
        ]

        for i in range(1024):
            data.append(self.protocol.buff_type.pack_varint(127))

        data.append(self.protocol.buff_type.pack_varint(0))
        data.append(b'')
        data.append(self.protocol.buff_type.pack_varint(0))
        data.append(b'')

        for x in range(-8, 8):
            for y in range(-8, 8):
                self.protocol.send_packet("chunk_data", self.protocol.buff_type.pack("ii", x, y), *data)
