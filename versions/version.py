import abc
import time

import json
from quarry.types.uuid import UUID

import config
from waitingserver import Protocol

class Version(object, metaclass=abc.ABCMeta):
    def __init__(self, protocol: Protocol):
        self.protocol = protocol
        self.uuid = UUID.from_offline_player('NotKatuen')
        self.viewpoint_id = 999

        self.current_world = None
        self.current_position = None
        self.raining = False

        self.player_spawned = False

        self.last_portal = 0
        self.last_command = 0
        self.last_teleport = 0

        self.version_name = None

    def player_joined(self):
        self.send_join_game()

        self.protocol.ticker.add_loop(100, self.send_keep_alive)  # Keep alive packets
        self.protocol.ticker.add_loop(200, self.send_stop_music)

        self.current_world = config.get_default_world(self.version_name)

        self.send_commands()
        self.send_world()

        self.protocol.ticker.add_delay(10, self.send_tablist)
        self.protocol.ticker.add_delay(20, self.send_end_music)

    def packet_player_position(self, buff):
        x = buff.unpack('d')
        y = buff.unpack('d')
        z = buff.unpack('d')

        buff.unpack('b') # on_ground

        self.check_portals(x, y, z)
        self.check_bounds(x, y, z)

    def packet_player_position_and_look(self, buff):
        x = buff.unpack('d')
        y = buff.unpack('d')
        z = buff.unpack('d')

        buff.unpack('f') # yaw
        buff.unpack('f') # pitch
        buff.unpack('b') # on_ground

        self.check_portals(x, y, z)
        self.check_bounds(x, y, z)

    # Handle /spawn and /reset commands
    def packet_chat_message(self, buff):
        message = buff.unpack_string()
        now = time.time()

        if message == "/spawn" or message == "/hub":
            if now - self.last_command < 0.5:
                return

            self.send_spawn()
        elif message == "/reset":
            if now - self.last_command < 2:
                return

            self.reset_world()
        else:
            return

        self.last_command = time.time()

    def check_bounds(self, x, y, z):
        if not self.current_world.is_within_bounds(x, y, z):
            self.send_spawn(True)

    def check_portals(self, x, y, z):
        server = self.current_world.get_portal_at(x, y, z)

        if server is not None:
            self.send_portal(server)

    def send_world(self):
        self.send_spawn()

        # Chunk packets
        for packet in self.current_world.packets:
            self.protocol.send_packet(packet.get('type'), packet.get('packet'))

        # Start/stop rain as necessary
        if self.current_world.weather == 'rain':
            if self.raining is False:
                self.protocol.send_packet('change_game_state', self.protocol.buff_type.pack("Bf", 2, 0))
                self.raining = True
        elif self.raining is True:
            self.protocol.send_packet('change_game_state', self.protocol.buff_type.pack("Bf", 1, 0))
            self.raining = False

        # Time of day
        self.protocol.send_packet('time_update',
                         self.protocol.buff_type.pack("Qq", 0,
                                             # Cycle
                                             self.current_world.time  if self.current_world.cycle is True
                                             else (0 - self.current_world.time)))

    def send_spawn(self, effects = False):
        spawn = self.current_world.spawn

        self.protocol.send_packet("player_position_and_look",
                        self.protocol.buff_type.pack("dddff?", spawn.get('x'), spawn.get('y'), spawn.get('z'), spawn.get('yaw'), spawn.get('pitch'), 0b00000),
                                self.protocol.buff_type.pack_varint(0))

        if effects is True:
            self.protocol.send_packet("effect",
                             self.protocol.buff_type.pack("i", 2003),
                             self.protocol.buff_type.pack_position(int(spawn.get('x')), int(spawn.get('y')), int(spawn.get('z'))),
                             self.protocol.buff_type.pack("ib", 0, False))

        self.player_spawned = True

    def reset_world(self):
        self.player_spawned = False
        self.raining = False

        self.send_respawn()

        self.protocol.ticker.add_delay(1, self.send_world)
        self.protocol.ticker.add_delay(2, self.send_reset_sound)
        self.protocol.ticker.add_delay(20, self.send_end_music)

    def send_tablist(self):
        self.protocol.send_packet("player_list_header_footer",
                         self.protocol.buff_type.pack_string(json.dumps({
                            "text": 'Gamers Online: ',
                            "extra": [
                                {
                                    "text": "123",
                                    "obfuscated": True,
                                    "color": "green"
                                },
                            ]
                        })),
                         self.protocol.buff_type.pack_string(json.dumps({"translate": ""})))

    def send_keep_alive(self):
        self.protocol.send_packet("keep_alive", self.protocol.buff_type.pack("Q", 0))

    def send_portal(self, server):
        now = time.time()

        if now - self.last_portal > 3:
            self.last_portal = now
            self.protocol.logger.info("Sending %s to %s.", self.protocol.display_name, server)

            connect = "Connect".encode('utf-8')
            server = server.encode('utf-8')
            message_format = 'H' + str(len(connect)) + 'sH' + str(len(server)) + 's'

            self.protocol.send_packet("plugin_message",
                             self.protocol.buff_type.pack_string('bungeecord:main'),
                             self.protocol.buff_type.pack(message_format, len(connect), connect, len(server), server))

    def send_end_music(self):
        spawn = self.current_world.spawn

        self.send_stop_music()
        self.protocol.send_packet("named_sound_effect",
                         self.protocol.buff_type.pack_string("minecraft:music.end"),
                         self.protocol.buff_type.pack_varint(2),
                         self.protocol.buff_type.pack("iiiff", int(spawn.get('x')), int(spawn.get('y')), int(spawn.get('z')), 100000.0, 1))


    def send_stop_music(self):
        self.protocol.send_packet("stop_sound", self.protocol.buff_type.pack("B", 2), self.protocol.buff_type.pack_string("minecraft:music.game"))
        self.protocol.send_packet("stop_sound", self.protocol.buff_type.pack("B", 2), self.protocol.buff_type.pack_string("minecraft:music.creative"))

    def send_reset_sound(self):
        spawn = self.current_world.spawn

        self.protocol.send_packet("named_sound_effect",
                         self.protocol.buff_type.pack_string("minecraft:item.trident.thunder"),
                         self.protocol.buff_type.pack_varint(6),
                         self.protocol.buff_type.pack("iiiff", int(spawn.get('x')), int(spawn.get('y')), int(spawn.get('z')),
                                             100000.0, 1))

    def send_commands(self):
        commands = {
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
            },
        }

        self.protocol.send_packet('declare_commands', self.protocol.buff_type.pack_commands(commands))

    @abc.abstractmethod
    def send_join_game(self):
        raise NotImplementedError('users must define send_join_game to use this base class')

    @abc.abstractmethod
    def send_respawn(self):
        raise NotImplementedError('users must define send_respawn to use this base class')
