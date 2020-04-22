"""
Empty server that send the _bare_ minimum data to keep a minecraft client connected
"""
import logging
import random
import time
import math
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

        self.last_click = time.time()
        self.last_portal = time.time()

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
        self.send_world()

    def player_left(self):
        super().player_left()

        set_players_online(len(self.factory.players))

    # Cycle through viewpoints when player clicks
    def packet_animation(self, buff):
        buff.unpack_varint()

    def packet_player_position(self, buff):
        x = buff.unpack('d')
        y = buff.unpack('d')
        z = buff.unpack('d')
        on_ground = buff.unpack('b')

        self.check_portals(x, y, z)

    def packet_player_position_and_look(self, buff):
        x = buff.unpack('d')
        y = buff.unpack('d')
        z = buff.unpack('d')
        yaw = buff.unpack('f')
        pitch = buff.unpack('f')
        on_ground = buff.unpack('b')

        self.check_portals(x, y, z)

    # Handle /next and /orev commands in voting mode
    def packet_chat_message(self, buff):
        message = buff.unpack_string()

        if message == "/spawn":
            self.send_spawn()

        if message == "/reset":
            self.reset_world()

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

    def send_spawn(self):
        spawn = self.current_world.spawn

        self.send_packet("player_position_and_look",
                        self.buff_type.pack("dddff?", spawn.get('x'), spawn.get('y'), spawn.get('z'), spawn.get('yaw'), spawn.get('pitch'), 0b00000),
                                self.buff_type.pack_varint(0))

        self.player_spawned = True

    def reset_world(self):
        self.player_spawned = False
        self.raining = False

        Connect
        self.send_packet("respawn", self.buff_type.pack("iBq", 0, 3, 0), self.buff_type.pack_string("flat"))
        self.send_world()

    def send_keep_alive(self):
        self.send_packet("keep_alive", self.buff_type.pack("Q", 0))

    def check_portals(self, x, y, z):
        x = math.floor(x)
        y = math.floor(y)
        z = math.floor(z)

        for portal in self.current_world.portals:
            pos1x = min(portal['pos1'][0], portal['pos2'][0])
            pos1y = min(portal['pos1'][1], portal['pos2'][1])
            pos1z = min(portal['pos1'][2], portal['pos2'][2])

            pos2x = max(portal['pos1'][0], portal['pos2'][0])
            pos2y = max(portal['pos1'][1], portal['pos2'][1])
            pos2z = max(portal['pos1'][2], portal['pos2'][2])

            if pos1x <= x <= pos2x and pos1y <= y <= pos2y and pos1z <= z <= pos2z :
                self.send_portal(portal['server'])

                return

    def send_portal(self, server):
        now = time.time()

        if now - self.last_portal > 3:
            self.last_portal = now
            self.logger.info("Sending %s to %s.", self.display_name, server)

            connect = bytes("Connect", 'utf-8')
            server = bytes(server, 'utf-8')

            self.send_packet("plugin_message",
                             self.buff_type.pack_string('bungeecord:main'),
                             self.buff_type.pack('HsHs', len(connect), connect, len(server), server))

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

