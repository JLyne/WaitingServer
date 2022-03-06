import os

from quarry.types.buffer import Buffer
from quarry.types.nbt import TagInt

from waitingserver.versions import Version_1_16_2
from waitingserver.versions.version import parent_folder


class Version_1_17(Version_1_16_2):
    protocol_version = 755
    chunk_format = '1.17'

    empty_chunk = None

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
        empty_chunk = self.__class__.get_empty_chunk()

        for x in range(-8, 8):
            for y in range(-8, 8):
                self.protocol.send_packet("chunk_data", self.protocol.buff_type.pack("ii", x, y), empty_chunk)

    @classmethod
    def get_empty_chunk(cls):
        if cls.empty_chunk is None:
            empty_chunk_buffer = Buffer(open(os.path.join(parent_folder, 'empty_chunk', cls.chunk_format + '.bin'), 'rb').read())
            empty_chunk_buffer.unpack("i")
            empty_chunk_buffer.unpack("i")

            cls.empty_chunk = empty_chunk_buffer.read()

        return cls.empty_chunk
