import os

from quarry.types.buffer import Buffer
from quarry.types.nbt import TagCompound, TagRoot, TagString, TagList, NBTFile, TagInt

from waitingserver.versions import Version_1_17_1
from waitingserver.versions.version import parent_folder


class Version_1_18(Version_1_17_1):
    protocol_version = 757
    chunk_format = '1.18'

    biomes = NBTFile(TagRoot({})).load(os.path.join(parent_folder, 'biomes', chunk_format + '.nbt'))

    empty_chunk_buffer = Buffer(open(os.path.join(parent_folder, 'empty_chunk', chunk_format + '.bin'), 'rb').read())
    empty_chunk_buffer.unpack("i")
    empty_chunk_buffer.unpack("i")

    empty_chunk = empty_chunk_buffer.read()

    def get_dimension_settings(self):
        settings = super().get_dimension_settings()

        settings['min_y'] = TagInt(-64)
        settings['height'] = TagInt(384)

        return settings

    def send_join_game(self):
        codec = TagRoot({
            '': TagCompound({
                'minecraft:dimension_type': TagCompound({
                    'type': TagString("minecraft:dimension_type"),
                    'value': TagList([
                        TagCompound(self.dimension)
                    ]),
                }),
                'minecraft:worldgen/biome': self.biomes.root_tag.body
            })
        })

        self.protocol.send_packet("join_game",
                                  self.protocol.buff_type.pack("i?BB", 0, False, 1, 1),
                                  self.protocol.buff_type.pack_varint(2),
                                  self.protocol.buff_type.pack_string("rtgame:waiting"),
                                  self.protocol.buff_type.pack_string("rtgame:reset"),
                                  self.protocol.buff_type.pack_nbt(codec),
                                  self.protocol.buff_type.pack_nbt(self.current_dimension),
                                  self.protocol.buff_type.pack_string("rtgame:waiting"),
                                  self.protocol.buff_type.pack("q", 0),
                                  self.protocol.buff_type.pack_varint(0),
                                  self.protocol.buff_type.pack_varint(32),
                                  self.protocol.buff_type.pack_varint(0),
                                  self.protocol.buff_type.pack("????", False, True, False, False))


