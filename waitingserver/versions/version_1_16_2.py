from quarry.data.data_packs import data_packs
from quarry.types.nbt import TagList, TagCompound, TagRoot, TagString, TagByte, TagFloat, TagInt

from waitingserver.versions import Version_1_16
from waitingserver.protocol import Protocol


class Version_1_16_2(Version_1_16):
    protocol_version = 751
    chunk_format = '1.16.2'

    def __init__(self, protocol: Protocol, bedrock: False):
        super(Version_1_16_2, self).__init__(protocol, bedrock)

        self.dimension_codec = None
        self.current_dimension = None

    def init_dimension_codec(self):
        self.dimension_codec = data_packs[self.protocol_version]

        self.dimension_codec.body.value['minecraft:dimension_type'] = TagCompound({
            'type': TagString("minecraft:dimension_type"),
            'value': TagList([
                TagCompound({
                    'name': TagString("minecraft:overworld"),
                    'id': TagInt(0),
                    'element': TagCompound(self.get_dimension_settings("overworld")),
                }),
                TagCompound({
                    'name': TagString("minecraft:nether"),
                    'id': TagInt(1),
                    'element': TagCompound(self.get_dimension_settings("nether")),
                }),
                TagCompound({
                    'name': TagString("minecraft:the_end"),
                    'id': TagInt(2),
                    'element': TagCompound(self.get_dimension_settings("the_end")),
                })
            ]),
        })

        # Make void sky and fog black
        for biome in self.dimension_codec.body.value['minecraft:worldgen/biome'].value['value'].value:
            if biome.value['name'].value == "minecraft:the_void":
                effects = biome.value['element'].value['effects']

                effects.value['sky_color'].value = effects.value['fog_color'].value = \
                    effects.value['water_color'].value = effects.value['water_fog_color'].value = 0

    def get_dimension_settings(self, name: str):
        settings = {
            'piglin_safe': TagByte(0),
            'natural': TagByte(1),
            'ambient_light': TagFloat(0.0),
            'infiniburn': TagString("minecraft:infiniburn_{}".format(name)),
            'respawn_anchor_works': TagByte(0),
            'has_skylight': TagByte(1),
            'bed_works': TagByte(0),
            "effects": TagString("minecraft:{}".format(name)),
            'has_raids': TagByte(0),
            'logical_height': TagInt(256),
            'coordinate_scale': TagFloat(1.0),
            'ultrawarm': TagByte(0),
            'has_ceiling': TagByte(0),
        }

        return settings

    def send_join_game(self):
        self.init_dimension_codec()

        self.protocol.send_packet("join_game",
                                  self.protocol.buff_type.pack("i?BB", 0, False, 1, 1),
                                  self.protocol.buff_type.pack_varint(2),
                                  self.protocol.buff_type.pack_string("rtgame:waiting"),
                                  self.protocol.buff_type.pack_string("rtgame:reset"),
                                  self.protocol.buff_type.pack_nbt(self.dimension_codec),
                                  self.protocol.buff_type.pack_nbt(self.current_dimension),
                                  self.protocol.buff_type.pack_string("rtgame:waiting"),
                                  self.protocol.buff_type.pack("q", 0),
                                  self.protocol.buff_type.pack_varint(0),
                                  self.protocol.buff_type.pack_varint(7),
                                  self.protocol.buff_type.pack("????", False, True, False, False))

    def send_respawn(self):
        self.init_dimension_codec()

        self.protocol.send_packet("respawn",
                                  self.protocol.buff_type.pack_nbt(self.current_dimension),
                                  self.protocol.buff_type.pack_string("rtgame:reset"),
                                  self.protocol.buff_type.pack("qBB", 0, 1, 1),
                                  self.protocol.buff_type.pack("???", False, False, True))

        self.protocol.send_packet("respawn",
                                  self.protocol.buff_type.pack_nbt(self.current_dimension),
                                  self.protocol.buff_type.pack_string("rtgame:waiting"),
                                  self.protocol.buff_type.pack("qBB", 0, 1, 1),
                                  self.protocol.buff_type.pack("???", False, False, True))
