import json

from quarry.types import chat
from quarry.types.nbt import TagRoot, TagCompound, TagInt
from quarry.types.uuid import UUID
from typing import List, Dict, Tuple, Union

from waitingserver.Map import MapPart
from waitingserver.direction import Direction
from waitingserver.versions import Version
from waitingserver.protocol import Protocol


class Version_1_15(Version):
    protocol_version = 578
    chunk_format = '1.15'
    map_format = '1.12'

    armor_stand_id = 1
    item_frame_id = 36
    map_item_id = 671

    def __init__(self, protocol: Protocol, bedrock: False):
        super(Version_1_15, self).__init__(protocol, bedrock)

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

    def send_join_game(self):
        self.protocol.send_packet("join_game",
                                  self.protocol.buff_type.pack("iBqiB", 0, 1, 0, 0, 0),
                                  self.protocol.buff_type.pack_string("default"),
                                  self.protocol.buff_type.pack_varint(7),
                                  self.protocol.buff_type.pack("??", False, True))

    def send_spawn(self):
        spawn = self.current_world.spawn

        self.protocol.send_packet("player_position_and_look",
                                  self.protocol.buff_type.pack("dddff?", spawn.get('x'), spawn.get('y'), spawn.get('z'),
                                                               spawn.get('yaw'), spawn.get('pitch'), 0b00000),
                                  self.protocol.buff_type.pack_varint(0))

    def send_spawn_effect(self):
        spawn = self.current_world.spawn

        self.protocol.send_packet("effect",
                                  self.protocol.buff_type.pack("i", 2003),
                                  self.protocol.buff_type.pack_position(
                                      int(spawn.get('x')),
                                      int(spawn.get('y')),
                                      int(spawn.get('z'))),
                                  self.protocol.buff_type.pack("ib", 0, False))

        self.send_global_sound("minecraft:entity.enderman.teleport", 6)

    def send_respawn(self):
        self.protocol.send_packet("respawn", self.protocol.buff_type.pack("iBq", 1, 0, 1),
                                  self.protocol.buff_type.pack_string("default"))
        self.protocol.send_packet("respawn", self.protocol.buff_type.pack("iBq", 0, 0, 1),
                                  self.protocol.buff_type.pack_string("default"))

    def send_reset_world(self):
        data = [
            self.protocol.buff_type.pack_varint(0),
            self.protocol.buff_type.pack_nbt(TagRoot({'': TagCompound({})})),
            self.protocol.buff_type.pack_varint(1024),
        ]

        for i in range(0, 1024):
            data.append(self.protocol.buff_type.pack_varint(127))

        data.append(self.protocol.buff_type.pack_varint(0))
        data.append(self.protocol.buff_type.pack_varint(0))

        for x in range(-8, 8):
            for y in range(-8, 8):
                self.protocol.send_packet("chunk_data", self.protocol.buff_type.pack("ii?", x, y, True), *data)

    def send_keep_alive(self):
        self.protocol.send_packet("keep_alive", self.protocol.buff_type.pack("Q", 0))

    def send_time(self):
        # Time of day
        self.protocol.send_packet('time_update',
                                  self.protocol.buff_type.pack("Qq", 0,
                                                               self.current_world.time
                                                               if self.current_world.cycle is True
                                                               else (0 - self.current_world.time)))

    def send_weather(self, rain=False):
        if rain:
            self.protocol.send_packet('change_game_state', self.protocol.buff_type.pack("Bf", 2, 0))
        else:
            self.protocol.send_packet('change_game_state', self.protocol.buff_type.pack("Bf", 1, 0))

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

        self.protocol.send_packet("named_sound_effect",
                                  self.protocol.buff_type.pack_string(sound),
                                  self.protocol.buff_type.pack_varint(channel),
                                  self.protocol.buff_type.pack("iiiff",
                                                               int(spawn.get('x')),
                                                               int(spawn.get('y')),
                                                               int(spawn.get('z')), 100000.0, 1))

    def send_commands(self):
        self.protocol.send_packet('declare_commands', self.protocol.buff_type.pack_commands(self.commands))

    def send_chat_message(self, message):
        self.protocol.send_packet('chat_message',
                                  self.protocol.buff_type.pack_string(message),
                                  self.protocol.buff_type.pack("b", 1))

    def send_tablist(self):
        self.protocol.send_packet("player_list_header_footer",
                                  self.protocol.buff_type.pack_string(json.dumps({
                                      "text": "\n\ue300\n"
                                  })),
                                  self.protocol.buff_type.pack_string(json.dumps({"translate": ""})))

        self.protocol.send_packet("player_list_item",
                                  self.protocol.buff_type.pack_varint(0),
                                  self.protocol.buff_type.pack_varint(1),
                                  self.protocol.buff_type.pack_uuid(self.protocol.uuid),
                                  self.protocol.buff_type.pack_string(self.protocol.display_name),
                                  self.protocol.buff_type.pack_varint(0),
                                  self.protocol.buff_type.pack_varint(1),
                                  self.protocol.buff_type.pack_varint(1),
                                  self.protocol.buff_type.pack_varint(0))

    def send_inventory(self):
        data = [
            self.protocol.buff_type.pack('Bh', 0, 46)
        ]

        for i in range(0, 46):
            data.append(self.protocol.buff_type.pack('?', False))

        self.protocol.send_packet('window_items', *data)

    def send_portal(self, server):
        connect = "Connect".encode('utf-8')
        server = server.encode('utf-8')
        message_format = 'H' + str(len(connect)) + 'sH' + str(len(server)) + 's'

        self.protocol.send_packet("plugin_message",
                                  self.protocol.buff_type.pack_string('bungeecord:main'),
                                  self.protocol.buff_type.pack(message_format, len(connect), connect, len(server),
                                                               server))

    def send_map_frame(self, pos: List[float], direction: Direction, map_id: int):
        self.protocol.send_packet("spawn_object",
                                  self.protocol.buff_type.pack_varint(self.last_entity_id),  # Entity id
                                  self.protocol.buff_type.pack_uuid(UUID.random()),  # Entity UUID
                                  self.protocol.buff_type.pack_varint(self.item_frame_id),  # Item frame
                                  self.protocol.buff_type.pack("dddbbihhh",
                                                               pos[0], pos[1], pos[2],  # Position
                                                               0, 0, int(direction),  # Rotation, facing
                                                               0, 0, 0))  # Velocity

        self.send_entity_metadata(self.last_entity_id, self.get_map_frame_metadata(map_id))
        self.last_entity_id += 1

    def get_map_frame_metadata(self, map_id: int) -> Dict[Tuple[int, int], Union[str, int, bool]]:
        map_nbt = TagRoot({
            '': TagCompound({
                'map': TagInt(map_id)
            })
        })

        return {
            (0, 0): 0x20,  # Invisible (index 0, type 0 (byte))
            (6, 8): {'item': self.map_item_id, 'count': 1, 'tag': map_nbt},  # Item (type 6 (slot), index 8)
        }

    def send_map_data(self, part: MapPart):
        if self.map_packets.get(self.map_format) is None:
            self.map_packets[self.map_format] = dict()

        if self.map_packets[self.map_format].get(part.map_id) is not None:
            self.protocol.send_packet("map", *self.map_packets[self.map_format][part.map_id])
            return

        data = [
            self.protocol.buff_type.pack_varint(part.map_id),
            self.protocol.buff_type.pack("b??BBBB", 0, True, False, 128, 128, 0, 0),
            self.protocol.buff_type.pack_varint(len(part.data))
        ]

        for i in range(0, 16384):
            data.append(self.protocol.buff_type.pack("B", part.data[i]))

        self.map_packets[self.map_format][part.map_id] = data
        self.protocol.send_packet("map", *data)

    def send_status_hologram(self, pos: List[float]):
        entity_id = self.last_entity_id
        self.protocol.send_packet("spawn_mob",
                                  self.protocol.buff_type.pack_varint(self.last_entity_id),  # Entity id
                                  self.protocol.buff_type.pack_uuid(UUID.random()),  # Entity UUID
                                  self.protocol.buff_type.pack_varint(self.armor_stand_id),  # Item frame
                                  self.protocol.buff_type.pack("dddbbbhhh",
                                                               pos[0], pos[1], pos[2],  # Position
                                                               0, 0, 0,  # Rotation, head facing
                                                               0, 0, 0))  # Velocity

        self.send_entity_metadata(entity_id, self.get_status_hologram_metadata())

        self.last_entity_id += 1
        return entity_id

    def send_entity_metadata(self, entity_id: int, metadata: Dict[Tuple[int, int], Union[str, int, bool]]):
        self.protocol.send_packet("entity_metadata",
                                  self.protocol.buff_type.pack_varint(entity_id),
                                  self.protocol.buff_type.pack_entity_metadata(metadata))

    @staticmethod
    def get_status_hologram_metadata(text: chat.Message = "") -> Dict[Tuple[int, int], Union[str, int, bool]]:
        return {
            (0, 0): 0x20,  # Custom name (index 0, type 0 (byte))
            (7, 5): True,  # No gravity (index 5, type 7 (boolean))
            (5, 2): text,  # Custom name (index 2, type 5 (optional chat))
            (7, 3): True,  # Custom name visible (index 3, type 7 (boolean))
        }

    def send_debug_marker(self, pos: List[int], name: str, r: int, g: int, b: int):
        encoded_color = 0
        encoded_color = encoded_color | b
        encoded_color = encoded_color | (g << 8)
        encoded_color = encoded_color | (r << 16)
        encoded_color = encoded_color | (255 << 24)

        self.protocol.send_packet("plugin_message",
                                  self.protocol.buff_type.pack_string("minecraft:debug/game_test_add_marker"),
                                  self.protocol.buff_type.pack_position(pos[0], pos[1], pos[2]),
                                  self.protocol.buff_type.pack("I", encoded_color),
                                  self.protocol.buff_type.pack_string(name),
                                  self.protocol.buff_type.pack("i", 2147483647))

    def clear_debug_markers(self):
        self.protocol.send_packet("plugin_message",
                                  self.protocol.buff_type.pack_string("minecraft:debug/game_test_clear"))
