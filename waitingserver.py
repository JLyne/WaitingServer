"""
Empty server that send the _bare_ minimum data to keep a minecraft client connected
"""
import time
from argparse import ArgumentParser
from copy import deepcopy

import config

from twisted.internet import reactor
from quarry.net.server import ServerFactory, ServerProtocol

from quarry.types.uuid import UUID

from prometheus import set_players_online, init_prometheus

worlds = list()

class StoneWallProtocol(ServerProtocol):
    def __init__(self, factory, remote_addr):
        self.uuid = UUID.from_offline_player('NotKatuen')
        self.viewpoint_id = 999

        self.current_world = None
        self.current_position = None
        self.raining = False

        self.player_spawned = False

        self.last_portal = 0
        self.last_command = 0
        self.last_teleport = 0

        self.forwarded_uuid = None
        self.forwarded_host = None

        super(StoneWallProtocol, self).__init__(factory, remote_addr)

    def packet_handshake(self, buff):
        buff2 = deepcopy(buff)
        super().packet_handshake(buff)

        p_protocol_version = buff2.unpack_varint()
        p_connect_host = buff2.unpack_string()

        if p_protocol_version != 578:
            self.close("Please use 1.15.2")

        # Bungeecord ip forwarding, ip/uuid is included in host string separated by \00s
        split_host = str.split(p_connect_host, "\00")

        if len(split_host) >= 3:
            host = split_host[1]
            online_uuid = split_host[2]

            self.forwarded_host = host
            self.forwarded_uuid = UUID.from_hex(online_uuid)

    def player_joined(self):
        # Overwrite with forwarded information if present
        if self.forwarded_uuid is not None:
            self.uuid = self.forwarded_uuid
            self.display_name_confirmed = True

        if self.forwarded_host is not None:
            self.connect_host = self.forwarded_host

        super().player_joined()

        set_players_online(len(self.factory.players))

        # Sent init packets
        self.send_packet("join_game",
                         self.buff_type.pack("iBqiB", 0, 1, 0, 0, 0),
                         self.buff_type.pack_string("default"),
                         self.buff_type.pack_varint(3),
                         self.buff_type.pack("??", False, True))

        self.ticker.add_loop(100, self.send_keep_alive)  # Keep alive packets

        self.current_world = config.get_default_world()
        self.send_commands()
        self.send_world()

    def player_left(self):
        super().player_left()

        set_players_online(len(self.factory.players))

    def packet_player_position(self, buff):
        x = buff.unpack('d')
        y = buff.unpack('d')
        z = buff.unpack('d')
        on_ground = buff.unpack('b')

        self.check_portals(x, y, z)
        self.check_bounds(x, y, z)

    def packet_player_position_and_look(self, buff):
        x = buff.unpack('d')
        y = buff.unpack('d')
        z = buff.unpack('d')
        yaw = buff.unpack('f')
        pitch = buff.unpack('f')
        on_ground = buff.unpack('b')

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

    def send_world(self):
        self.send_spawn()

        # Chunk packets
        for packet in self.current_world.packets:
            self.send_packet(packet.get('type'), packet.get('packet'))

        # Start/stop rain as necessary
        if self.current_world.weather == 'rain':
            if self.raining is False:
                self.send_packet('change_game_state', self.buff_type.pack("Bf", 2, 0))
                self.raining = True
        elif self.raining is True:
            self.send_packet('change_game_state', self.buff_type.pack("Bf", 1, 0))
            self.raining = False

        # Time of day
        self.send_packet('time_update',
                         self.buff_type.pack("Qq", 0,
                                             # Cycle
                                             self.current_world.time  if self.current_world.cycle is True
                                             else (0 - self.current_world.time)))

    def send_spawn(self, effects = False):
        spawn = self.current_world.spawn

        self.send_packet("player_position_and_look",
                        self.buff_type.pack("dddff?", spawn.get('x'), spawn.get('y'), spawn.get('z'), spawn.get('yaw'), spawn.get('pitch'), 0b00000),
                                self.buff_type.pack_varint(0))

        if effects is True:
            self.send_packet("effect",
                             self.buff_type.pack("i", 2003),
                             self.buff_type.pack_position(int(spawn.get('x')), int(spawn.get('y')), int(spawn.get('z'))),
                             self.buff_type.pack("ib", 0, False))

        self.player_spawned = True

    def reset_world(self):
        self.player_spawned = False
        self.raining = False

        self.send_packet("respawn", self.buff_type.pack("iBq", 1, 0, 1), self.buff_type.pack_string("default"))
        self.send_packet("respawn", self.buff_type.pack("iBq", 0, 0, 1), self.buff_type.pack_string("default"))

        self.ticker.add_delay(1, self.send_world)
        self.ticker.add_delay(2, self.send_reset_sound)

    def send_reset_sound(self):
        spawn = self.current_world.spawn

        self.send_packet("named_sound_effect",
                         self.buff_type.pack_string("minecraft:item.trident.thunder"),
                         self.buff_type.pack_varint(6),
                         self.buff_type.pack("iiiff", int(spawn.get('x')), int(spawn.get('y')), int(spawn.get('z')), 100000.0, 1))

    def send_keep_alive(self):
        self.send_packet("keep_alive", self.buff_type.pack("Q", 0))

    def send_portal(self, server):
        now = time.time()

        if now - self.last_portal > 3:
            self.last_portal = now
            self.logger.info("Sending %s to %s.", self.display_name, server)

            connect = "Connect".encode('utf-8')
            server = server.encode('utf-8')
            message_format = 'H' + str(len(connect)) + 'sH' + str(len(server)) + 's'

            self.send_packet("plugin_message",
                             self.buff_type.pack_string('bungeecord:main'),
                             self.buff_type.pack(message_format, len(connect), connect, len(server), server))

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

        self.send_packet('declare_commands', self.buff_type.pack_commands(commands))

    def check_bounds(self, x, y, z):
        if not self.current_world.is_within_bounds(x, y, z):
            self.send_spawn(True)

    def check_portals(self, x, y, z):
        server = self.current_world.get_portal_at(x, y, z)

        if server is not None:
            self.send_portal(server)

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-a", "--host", default="127.0.0.1", help="bind address")
    parser.add_argument("-p", "--port", default=25567, type=int, help="bind port")
    parser.add_argument("-m", "--max", default=65535, type=int, help="player count")
    parser.add_argument("-r", "--metrics", default=None, type=int, help="expose prometheus metrics on specified port")

    args = parser.parse_args()

    server_factory = ServerFactory()
    server_factory.protocol = StoneWallProtocol
    server_factory.max_players = args.max
    server_factory.motd = "Waiting Server"
    server_factory.online_mode = False
    server_factory.compression_threshold = 5646848

    metrics_port = args.metrics

    config.load_world_config()
    worlds = config.get_worlds()

    if metrics_port is not None:
        init_prometheus(metrics_port)

    server_factory.listen(args.host, args.port)
    print('Server started')
    print("Listening on {}:{}".format(args.host, args.port))
    reactor.run()

