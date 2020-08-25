from quarry.types.nbt import TagList, TagCompound, TagRoot, TagString, TagByte, TagFloat, TagInt

from versions import Version_1_16
from waitingserver import Protocol

class Version_1_16_2(Version_1_16):
    def __init__(self, protocol: Protocol, bedrock: False):
        super(Version_1_16_2, self).__init__(protocol, bedrock)
        self.version_name = '1.16.2'

        self.dimension_settings = {
            'piglin_safe': TagByte(0),
            'natural': TagByte(1),
            'ambient_light': TagFloat(0.0),
            'infiniburn': TagString("minecraft:infiniburn_overworld"),
            'respawn_anchor_works': TagByte(0),
            'has_skylight': TagByte(0),
            'bed_works': TagByte(0),
            "effects": TagString("minecraft:overworld") if self.is_bedrock else TagString("minecraft:the_nether"),
            'has_raids': TagByte(0),
            'logical_height': TagInt(256),
            'coordinate_scale': TagFloat(1.0),
            'ultrawarm': TagByte(0),
            'has_ceiling': TagByte(0),
        }

        self.dimension = {
            'name': TagString("minecraft:overworld"),
            'id': TagInt(0),
            'element': TagCompound(self.dimension_settings),
        }

        self.current_dimension = TagRoot({
            '': TagCompound(self.dimension_settings),
        })

        self.biomes = [
            TagCompound({
                'name': TagString("minecraft:plains"),
                'id': TagInt(1),
                'element': TagCompound({
                    'precipitation': TagString("none"),
                    'effects': TagCompound({
                        'sky_color': TagInt(0),
                        'water_fog_color': TagInt(0),
                        'fog_color': TagInt(0),
                        'water_color': TagInt(0),
                    }),
                    'depth': TagFloat(0.1),
                    'temperature': TagFloat(0.5),
                    'scale': TagFloat(0.2),
                    'downfall': TagFloat(0.5),
                    'category': TagString("plains")
                }),
            }),
            TagCompound({
                'name': TagString("minecraft:the_void"),
                'id': TagInt(127),
                'element': TagCompound({
                    'precipitation': TagString("none"),
                    'effects': TagCompound({
                        'sky_color': TagInt(0),
                        'water_fog_color': TagInt(0),
                        'fog_color': TagInt(0),
                        'water_color': TagInt(0),
                    }),
                    'depth': TagFloat(0.1),
                    'temperature': TagFloat(0.5),
                    'scale': TagFloat(0.2),
                    'downfall': TagFloat(0.5),
                    'category': TagString("none")
                }),
            }),
        ]

    def send_join_game(self):
        codec = TagRoot({
            '': TagCompound({
                'minecraft:dimension_type': TagCompound({
                    'type': TagString("minecraft:dimension_type"),
                    'value': TagList([
                        TagCompound(self.dimension)
                    ]),
                }),
                'minecraft:worldgen/biome': TagCompound({
                    'type': TagString("minecraft:worldgen/biome"),
                    'value': TagList(self.biomes),
                })
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
                         self.protocol.buff_type.pack("????", False, True, False, False))

    def send_respawn(self):
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