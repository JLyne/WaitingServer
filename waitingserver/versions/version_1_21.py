from copy import deepcopy
from typing import List, Dict, Tuple, Union

from quarry.data.data_packs import vanilla_data_packs, pack_formats
from quarry.types.chat import Message
from quarry.types.data_pack import DataPack
from quarry.types.namespaced_key import NamespacedKey
from quarry.types.nbt import TagRoot, TagCompound, TagInt, TagString, TagByte, TagFloat
from quarry.types.uuid import UUID

from waitingserver.Map import MapPart
from waitingserver.direction import Direction
from waitingserver.protocol import Protocol
from waitingserver.versions import Version


class Version_1_21(Version):
    protocol_version = 767
    chunk_format = '1.21'
    map_format = '1.17'

    hologram_entity_id = 105  # Text display
    hologram_y_offset = 0  # Offset position by armor stand height
    map_entity_id = 47  # Glow item frame
    map_item_id = 982  # Filled map

    data_pack: DataPack = None  # Data pack to apply

    def __init__(self, protocol: Protocol, bedrock: bool = False):
        super().__init__(protocol, bedrock)

        self.commands = {
            "name": None,
            "suggestions": None,
            "type": "root",
            "executable": True,
            "redirect": None,
            "children": {
                "reset": {
                    "type": "literal",
                    "name": "reset",
                    "executable": True,
                    "redirect": None,
                    "children": dict(),
                    "suggestions": None
                },
                "spawn": {
                    "type": "literal",
                    "name": "spawn",
                    "executable": True,
                    "redirect": None,
                    "children": dict(),
                    "suggestions": None
                },
                "hub": {
                    "type": "literal",
                    "name": "hub",
                    "executable": True,
                    "redirect": None,
                    "children": dict(),
                    "suggestions": None
                },
                "unlink": {
                    "type": "literal",
                    "name": "unlink",
                    "executable": True,
                    "redirect": None,
                    "children": dict(),
                    "suggestions": None
                },
                "credits": {
                    "type": "literal",
                    "name": "credits",
                    "executable": True,
                    "redirect": None,
                    "children": dict(),
                    "suggestions": None
                },
            }
        }

        if self.protocol.voting_mode is True:
            self.commands["children"]["next"] = {
                "type": "literal",
                "name": "next",
                "executable": True,
                "redirect": None,
                "children": dict(),
                "suggestions": None
            }

            self.commands["children"]["prev"] = {
                "type": "literal",
                "name": "prev",
                "executable": True,
                "redirect": None,
                "children": dict(),
                "suggestions": None
            }

    def get_data_pack(self):
        if self.data_pack:
            return self.data_pack

        vanilla_pack = vanilla_data_packs[self.protocol_version]

        # Make void sky and fog black
        void = deepcopy(vanilla_pack.contents[NamespacedKey.minecraft('worldgen/biome')]
                        .get(NamespacedKey.minecraft('the_void')))

        effects = void['effects']
        effects['sky_color'] = effects['fog_color'] = effects['water_color'] = effects['water_fog_color'] = 2147483647

        contents = {
            NamespacedKey.minecraft('dimension_type'): {
                NamespacedKey.minecraft('overworld'): self.get_dimension_settings('overworld'),
                NamespacedKey.minecraft('the_nether'): self.get_dimension_settings('the_nether'),
                NamespacedKey.minecraft('the_end'): self.get_dimension_settings('the_end'),
            },
            NamespacedKey.minecraft('worldgen/biome'): {
                NamespacedKey.minecraft('the_void'): void
            }
        }

        self.data_pack = DataPack(NamespacedKey("rtgame", "waitingserver"), "1.0", pack_formats[self.protocol_version], contents)
        return self.data_pack

    def get_dimension_settings(self, name: str):
        return {
            'piglin_safe': TagByte(0),
            'natural': TagByte(1),
            'ambient_light': TagFloat(0.0),
            'respawn_anchor_works': TagByte(0),
            'has_skylight': TagByte(1),
            'bed_works': TagByte(0),
            "effects": TagString("minecraft:{}".format(name)),
            'has_raids': TagByte(0),
            'logical_height': TagInt(384),
            'coordinate_scale': TagFloat(1.0),
            'ultrawarm': TagByte(0),
            'has_ceiling': TagByte(0),
            'min_y': TagInt(-64),
            'height': TagInt(384),
            'infiniburn': TagString("#minecraft:infiniburn_{}".format(name)),
            'monster_spawn_block_light_limit': TagInt(0),
            'monster_spawn_light_level': TagInt(0)
        }

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
                                  self.protocol.buff_type.pack_varint(id),  # Now varint
                                  self.protocol.buff_type.pack_string("rtgame:waiting"),
                                  self.protocol.buff_type.pack("qBb??", 0, 1, 1, False, False),
                                  self.protocol.buff_type.pack("?", False),
                                  self.protocol.buff_type.pack_varint(0),
                                  self.protocol.buff_type.pack("?", False))  # Disable secure chat

    def send_spawn(self, effects=False):
        spawn = self.current_world.spawn

        self.protocol.send_packet("set_default_spawn_position",
                                  self.protocol.buff_type.pack("iii", int(spawn.get('x')), int(spawn.get('y')),
                                                               int(spawn.get('z'))))

        self.protocol.send_packet("player_position",
                                  self.protocol.buff_type.pack("dddff?",
                                                               spawn.get('x') + 0.5, spawn.get('y'), spawn.get('z') + 0.5,
                                                               spawn.get('yaw'), spawn.get('pitch'), 0b00000),
                                  self.protocol.buff_type.pack_varint(0))

        if effects is True:
            self.send_spawn_effect()

        self.protocol.send_packet("game_event", self.protocol.buff_type.pack("Bf", 13, 0.0))

    def send_spawn_effect(self):
        spawn = self.current_world.spawn

        self.protocol.send_packet("level_event",
                                  self.protocol.buff_type.pack("i", 2003),
                                  self.protocol.buff_type.pack_position(
                                      int(spawn.get('x')),
                                      int(spawn.get('y')),
                                      int(spawn.get('z'))),
                                  self.protocol.buff_type.pack("ib", 0, False))

        self.send_global_sound("minecraft:entity.enderman.teleport", 6)

    def send_respawn(self):
        dimension_registry = self.protocol.data_packs.get_registry(NamespacedKey.minecraft('dimension_type'))
        id = list(dimension_registry).index(self.current_world.dimension)

        self.protocol.send_packet("respawn",
                                  self.protocol.buff_type.pack_varint(id), # Now varint
                                  self.protocol.buff_type.pack_string("rtgame:reset"),
                                  self.protocol.buff_type.pack("qBB", 0, 1, 1),
                                  self.protocol.buff_type.pack("???", False, False, False),
                                  self.protocol.buff_type.pack_varint(0),
                                  self.protocol.buff_type.pack("b", 0))

        self.protocol.send_packet("respawn",
                                  self.protocol.buff_type.pack_varint(id), # Now varint
                                  self.protocol.buff_type.pack_string("rtgame:waiting"),
                                  self.protocol.buff_type.pack("qBB", 0, 1, 1),
                                  self.protocol.buff_type.pack("???", False, False, False),
                                  self.protocol.buff_type.pack_varint(0),
                                  self.protocol.buff_type.pack("b", 0))

    def send_reset_world(self):
        data = [
            self.protocol.buff_type.pack_nbt(TagRoot({'': TagCompound({})})),  # Heightmap
            self.protocol.buff_type.pack_varint(0),  # Data size
            self.protocol.buff_type.pack_varint(0),  # Block entity count
            self.protocol.buff_type.pack_varint(0),  # Sky light mask
            self.protocol.buff_type.pack_varint(0),  # Block light mask
            self.protocol.buff_type.pack_varint(0),  # Empty sky light mask
            self.protocol.buff_type.pack_varint(0),  # Empty block light mask
            self.protocol.buff_type.pack_varint(0),  # Sky light array count
            self.protocol.buff_type.pack_varint(0),  # Block light array count
        ]

        for x in range(-8, 8):
            for y in range(-8, 8):
                self.protocol.send_packet("level_chunk_with_light", self.protocol.buff_type.pack("ii", x, y), *data)

    def send_keep_alive(self):
        self.protocol.send_packet("keep_alive", self.protocol.buff_type.pack("Q", 0))

    def send_time(self):
        # Time of day
        self.protocol.send_packet('set_time',
                                  self.protocol.buff_type.pack("Qq", 0,
                                                               self.current_world.time
                                                               if self.current_world.cycle is True
                                                               else (0 - self.current_world.time)))

    def send_weather(self, rain=False):
        if rain:
            self.protocol.send_packet('game_event', self.protocol.buff_type.pack("Bf", 2, 0))
        else:
            self.protocol.send_packet('game_event', self.protocol.buff_type.pack("Bf", 1, 0))

    def send_music(self, stop=False):
        self.protocol.send_packet("stop_sound", self.protocol.buff_type.pack("B", 2),
                                  self.protocol.buff_type.pack_string("minecraft:music.game"))
        self.protocol.send_packet("stop_sound", self.protocol.buff_type.pack("B", 2),
                                  self.protocol.buff_type.pack_string("minecraft:music.creative"))

        if stop is False:
            self.send_global_sound(self.current_world.music, 2)

    def send_reset_sound(self):
        self.send_global_sound("minecraft:item.trident.thunder", 6)

    def send_global_sound(self, sound: str, channel: int):
        spawn = self.current_world.spawn

        self.protocol.send_packet("sound",
                                  self.protocol.buff_type.pack_varint(0),
                                  self.protocol.buff_type.pack_string(sound),
                                  self.protocol.buff_type.pack("?", False),
                                  self.protocol.buff_type.pack_varint(channel),
                                  self.protocol.buff_type.pack("iiiffq",
                                                               int(spawn.get('x')),
                                                               int(spawn.get('y')),
                                                               int(spawn.get('z')), 100000.0, 1,
                                                               0))

    def send_commands(self):
        self.protocol.send_packet('commands', self.protocol.buff_type.pack_commands(self.commands))

    def send_chat_message(self, message: Message):
        self.protocol.send_packet('system_chat',
                                  self.protocol.buff_type.pack_chat(message),
                                  self.protocol.buff_type.pack("?", False))  # Not an overlay (action bar) message

    def send_tablist(self):
        self.protocol.send_packet("tab_list",
                                  self.protocol.buff_type.pack_chat("\n\ue300\n"),
                                  self.protocol.buff_type.pack_chat(""))

        self.protocol.send_packet("player_info_update",
                                  self.protocol.buff_type.pack('B', 63),
                                  self.protocol.buff_type.pack_varint(1),
                                  self.protocol.buff_type.pack_uuid(self.protocol.uuid),
                                  self.protocol.buff_type.pack_string(self.protocol.display_name),
                                  self.protocol.buff_type.pack_varint(0),
                                  self.protocol.buff_type.pack("?", False),  # No chat session info
                                  self.protocol.buff_type.pack_varint(1),
                                  self.protocol.buff_type.pack("?", True),  # Show in tab list
                                  self.protocol.buff_type.pack_varint(1),
                                  self.protocol.buff_type.pack("?", False))

    def send_inventory(self):
        data = [
            self.protocol.buff_type.pack('B', 0),
            self.protocol.buff_type.pack_varint(0),
            self.protocol.buff_type.pack_varint(46)
        ]

        for i in range(0, 46):
            data.append(self.protocol.buff_type.pack('?', False))

        data.append(self.protocol.buff_type.pack('?', False))
        self.protocol.send_packet('container_set_content', *data)

    def send_portal(self, server):
        connect = "Connect".encode('utf-8')
        server = server.encode('utf-8')
        message_format = 'H' + str(len(connect)) + 'sH' + str(len(server)) + 's'

        self.protocol.send_packet("custom_payload",
                                  self.protocol.buff_type.pack_string('bungeecord:main'),
                                  self.protocol.buff_type.pack(message_format, len(connect), connect, len(server),
                                                               server))

    def send_map_frame(self, pos: List[float], direction: Direction, map_id: int):
        self.protocol.send_packet("add_entity",
                                  self.protocol.buff_type.pack_varint(self.last_entity_id),
                                  self.protocol.buff_type.pack_uuid(UUID.random()),
                                  self.protocol.buff_type.pack_varint(self.map_entity_id),
                                  self.protocol.buff_type.pack("dddbbb", pos[0], pos[1], pos[2], 0, 0, 0),
                                  self.protocol.buff_type.pack_varint(int(direction)),
                                  self.protocol.buff_type.pack("hhh", 0, 0, 0))

        self.send_entity_metadata(self.last_entity_id, self.get_map_frame_metadata(map_id))
        self.last_entity_id += 1

    def get_map_frame_metadata(self, map_id: int) -> Dict[Tuple[int, int], Union[str, int, bool]]:
        return {
            (0, 0): 0x20,  # Invisible (index 0, type 0 (byte))
            (7, 8): {'item': self.map_item_id, 'count': 1, 'structured_data': {
                'map_id': map_id
            }},  # Item (type 7 (slot), index 8)
        }

    def send_map_data(self, part: MapPart):
        if self.map_packets.get(self.map_format) is None:
            self.map_packets[self.map_format] = dict()

        if self.map_packets[self.map_format].get(part.map_id) is not None:
            self.protocol.send_packet("map_item_data", *self.map_packets[self.map_format][part.map_id])
            return

        data = [
            self.protocol.buff_type.pack_varint(part.map_id),
            self.protocol.buff_type.pack("b??BBBB", 0, True, False, 128, 128, 0, 0),
            self.protocol.buff_type.pack_varint(len(part.data))
        ]

        for i in range(0, 16384):
            data.append(self.protocol.buff_type.pack("B", part.data[i]))

        self.map_packets[self.map_format][part.map_id] = data
        self.protocol.send_packet("map_item_data", *data)

    def send_status_hologram(self, pos: List[float]):
        entity_id = self.last_entity_id
        self.protocol.send_packet("add_entity",
                                  self.protocol.buff_type.pack_varint(self.last_entity_id),
                                  self.protocol.buff_type.pack_uuid(UUID.random()),
                                  self.protocol.buff_type.pack_varint(self.hologram_entity_id),
                                  self.protocol.buff_type.pack("dddbbb", pos[0], pos[1], pos[2], 0, 0, 0),
                                  self.protocol.buff_type.pack_varint(0),
                                  self.protocol.buff_type.pack("hhh", 0, 0, 0))

        self.send_entity_metadata(entity_id, self.get_status_hologram_metadata())

        self.last_entity_id += 1
        return entity_id

    def send_entity_metadata(self, entity_id: int, metadata: Dict[Tuple[int, int], Union[str, int, bool]]):
        self.protocol.send_packet("set_entity_data",
                                  self.protocol.buff_type.pack_varint(entity_id),
                                  self.protocol.buff_type.pack_entity_metadata(metadata))

    @staticmethod
    def get_status_hologram_metadata(text: Message = "") -> Dict[Tuple[int, int], Union[str, int, bool]]:
        return {
            (5, 23): text,  # Text (index 23, type 5 (chat))
            (1, 24): 150,  # Max width
            (0, 15): 3,
        }

    def send_debug_marker(self, pos: List[int], name: str, r: int, g: int, b: int):
        encoded_color = 0
        encoded_color = encoded_color | b
        encoded_color = encoded_color | (g << 8)
        encoded_color = encoded_color | (r << 16)
        encoded_color = encoded_color | (255 << 24)

        self.protocol.send_packet("custom_payload",
                                  self.protocol.buff_type.pack_string("minecraft:debug/game_test_add_marker"),
                                  self.protocol.buff_type.pack_position(pos[0], pos[1], pos[2]),
                                  self.protocol.buff_type.pack("I", encoded_color),
                                  self.protocol.buff_type.pack_string(name),
                                  self.protocol.buff_type.pack("i", 2147483647))

    def clear_debug_markers(self):
        self.protocol.send_packet("custom_payload",
                                  self.protocol.buff_type.pack_string("minecraft:debug/game_test_clear"))
