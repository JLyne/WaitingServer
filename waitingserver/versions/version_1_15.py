import json

from quarry.types.nbt import TagRoot, TagCompound, TagInt
from quarry.types.uuid import UUID
from typing import List

from waitingserver.Map import MapPart
from waitingserver.direction import Direction
from waitingserver.versions import Version
from waitingserver.protocol import Protocol


class Version_1_15(Version):
    protocol_version = 578
    chunk_format = '1.15'
    map_format = '1.12'

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

        self.protocol.send_packet("named_sound_effect",
                                  self.protocol.buff_type.pack_string("minecraft:entity.enderman.teleport"),
                                  self.protocol.buff_type.pack_varint(6),
                                  self.protocol.buff_type.pack("iiiff",
                                                               int(spawn.get('x')),
                                                               int(spawn.get('y')),
                                                               int(spawn.get('z')), 100000.0, 1))

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
        spawn = self.current_world.spawn

        self.protocol.send_packet("stop_sound", self.protocol.buff_type.pack("B", 2),
                                  self.protocol.buff_type.pack_string("minecraft:music.game"))
        self.protocol.send_packet("stop_sound", self.protocol.buff_type.pack("B", 2),
                                  self.protocol.buff_type.pack_string("minecraft:music.creative"))

        if stop is False:
            self.protocol.send_packet("named_sound_effect",
                                      self.protocol.buff_type.pack_string(self.current_world.music),
                                      self.protocol.buff_type.pack_varint(2),
                                      self.protocol.buff_type.pack("iiiff",
                                                                   int(spawn.get('x')),
                                                                   int(spawn.get('y')),
                                                                   int(spawn.get('z')), 100000.0, 1))

    def send_reset_sound(self):
        spawn = self.current_world.spawn

        self.protocol.send_packet("named_sound_effect",
                                  self.protocol.buff_type.pack_string("minecraft:item.trident.thunder"),
                                  self.protocol.buff_type.pack_varint(6),
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

        map_nbt = TagRoot({
            '': TagCompound({
                'map': TagInt(map_id)
            })
        })

        self.protocol.send_packet("entity_metadata",
                                  self.protocol.buff_type.pack_varint(self.last_entity_id),  # Entity id
                                  self.protocol.buff_type.pack("B", 0),  # Index 0, entity flags
                                  self.protocol.buff_type.pack_varint(0),  # Type byte
                                  self.protocol.buff_type.pack_varint(0x20),  # Value 0x20 - Invisible
                                  self.protocol.buff_type.pack("B", 8),  # Index 8, item frame item
                                  self.protocol.buff_type.pack_varint(6),  # Type slot
                                  self.protocol.buff_type.pack("?", True),  # Item exists
                                  self.protocol.buff_type.pack_varint(self.map_item_id),  # Filled map item id
                                  self.protocol.buff_type.pack("b", 1),  # Item count
                                  self.protocol.buff_type.pack_nbt(map_nbt),
                                  self.protocol.buff_type.pack("B", 0xff))  # End of packet

        self.last_entity_id += 1

    def send_map_data(self, part: MapPart):
        data = [
            self.protocol.buff_type.pack_varint(part.map_id),
            self.protocol.buff_type.pack("b??BBBB", 0, True, False, 128, 128, 0, 0),
            self.protocol.buff_type.pack_varint(len(part.data))
        ]

        for i in range(0, 16384):
            data.append(self.protocol.buff_type.pack("B", part.data[i]))

        self.protocol.send_packet("map", *data)
