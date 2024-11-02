import abc
import math
import time
from copy import deepcopy
from pathlib import Path

from quarry.types import chat
from typing import List, Dict, Tuple, Union, Optional

from quarry.types.chat import Message
from quarry.types.data_pack import DataPack

from waitingserver.Map import Map, MapPart
from waitingserver.direction import Direction
from waitingserver.protocol import Protocol
from waitingserver.config import get_default_world, worlds, maps
from waitingserver.voting import entry_component, entry_navigation_component

parent_folder = Path(__file__).parent.parent


class Version(object, metaclass=abc.ABCMeta):
    protocol_version = None
    chunk_format = None # Subfolder to use when sending packets for a world
    map_format = None # Subfolder to use when sending maps for a world

    hologram_entity_id = None # Entity ID to use when creating holograms
    hologram_y_offset = None # Vertical offset for hologram position
    map_entity_id = None # Entity ID to use when creating maps
    map_item_id = None # Item ID to use for the maps themselves

    map_packets = dict() # Map packet cache

    def __init__(self, protocol: Protocol, bedrock: False):
        self.protocol = protocol

        self.current_world = None

        self.last_portal = 0
        self.last_command = 0

        self.is_bedrock = bedrock

        self.last_entity_id = 1000
        self.status_holograms = dict()

    def player_joined(self):
        self.protocol.ticker.add_loop(100, self.send_keep_alive)  # Keep alive packets
        self.protocol.ticker.add_loop(200, lambda: self.send_music(True))

        if self.protocol.voting_mode:
            self.current_world = worlds[self.chunk_format][0]
        else:
            self.current_world = get_default_world(self.chunk_format)

        if self.current_world is None:
            self.protocol.close('No defined worlds compatible with current client version')
            return

        self.send_join_game()
        self.send_commands()
        self.send_world()

        if self.is_bedrock:  # Prevent geyser persisting previous server inventory
            self.send_inventory()

        self.protocol.ticker.add_delay(10, self.send_tablist)
        self.protocol.ticker.add_delay(20, self.send_music)

    def packet_move_player_pos(self, buff):
        x = buff.unpack('d')
        y = buff.unpack('d')
        z = buff.unpack('d')

        buff.unpack('b')  # on_ground

        self.check_portals(x, y, z)
        self.check_bounds(x, y, z)

    def packet_move_player_pos_rot(self, buff):
        x = buff.unpack('d')
        y = buff.unpack('d')
        z = buff.unpack('d')

        buff.unpack('f')  # yaw
        buff.unpack('f')  # pitch
        buff.unpack('b')  # on_ground

        self.check_portals(x, y, z)
        self.check_bounds(x, y, z)

    # Handle /spawn and /reset commands
    def packet_chat(self, buff):
        message = buff.unpack_string()
        buff.read()

        if message[0] == "/":
            self.handle_command(message[0:])

    # 1.19+
    def packet_chat_command(self, buff):
        command = buff.unpack_string()
        buff.read()

        self.handle_command(command)

    def handle_command(self, command: str):
        now = time.time()

        if command == "spawn" or command == "hub":
            if now - self.last_command < 0.5:
                return

            self.spawn_player(True)
        elif command == "reset":
            if now - self.last_command < 2:
                return

            self.reset_world(effects=True)

        elif command == "credits":
            if now - self.last_command < 0.5:
                return

            self.send_chat_message(self.current_world.credit_component())

        elif self.protocol.voting_mode is True:
            if command == "prev":
                self.previous_world()
            elif command == "next":
                self.next_world()

        self.last_command = time.time()

    def check_bounds(self, x, y, z):
        if not self.current_world.is_within_bounds(x, y, z):
            self.spawn_player(True)

    def check_portals(self, x, y, z):
        server = self.current_world.get_portal_at(x, y, z)
        now = time.time()

        if server is not None and now - self.last_portal > 3:
            self.last_portal = now
            self.protocol.logger.info("Sending %s to %s.", self.protocol.display_name, server)
            self.send_portal(server)

    def send_world(self):
        # Clear geyser chunk cache from previous server
        if self.is_bedrock:
            self.send_reset_world()

            # Fixes client getting stuck when crossing 0
            self.protocol.send_packet('initialize_border',
                                  self.protocol.buff_type.pack('dddd', 500, 500, 500, 500),
                                  self.protocol.buff_type.pack_varint(0),
                                  self.protocol.buff_type.pack_varint(29999984),
                                  self.protocol.buff_type.pack_varint(29999984),
                                  self.protocol.buff_type.pack_varint(1))

        # Chunk packets
        for packet in self.current_world.packets:
            self.protocol.send_packet(packet.type, packet.data)

        self.spawn_player()
        self.send_maps()
        self.send_status_holograms()
        self.send_status_hologram_texts()

        if self.protocol.debug_mode:
            self.send_debug_markers()

        # Start/stop rain as necessary
        self.send_weather(self.current_world.weather == 'rain')

        if self.is_bedrock:  # Current versions of geyser seem to ignore the time sometimes. Send repeatedly for now.
            self.protocol.ticker.add_loop(100, self.send_time)
        else:
            self.send_time()

        # Credits and entry navigation
        if self.protocol.voting_mode:
            self.send_chat_message(entry_component(
                worlds[self.chunk_format].index(self.current_world) + 1,
                len(worlds[self.chunk_format])))

            self.send_chat_message(self.current_world.credit_component())

            if not self.is_bedrock:
                self.send_chat_message(entry_navigation_component(self.protocol.uuid, self.protocol.voting_secret))

    def send_maps(self):
        if self.map_format is None:
            return

        maps_to_send = set()

        for world_map in self.current_world.maps:
            if world_map.map_name not in maps[self.map_format]:
                self.protocol.logger.info('Skipping spawn of unknown map {}'.format(world_map.map_name))
                continue

            map = maps[self.map_format][world_map.map_name]

            for x in range(0, map.width):
                for y in range(0, map.height):
                    pos = Map.get_spawn_pos(world_map.pos, world_map.direction, x, y)

                    self.send_map_frame(pos, world_map.direction, map.maps[(x * y) + x].map_id)

                    if self.protocol.debug_mode:
                        self.send_debug_marker([math.floor(pos[0]), math.floor(pos[1]), math.floor(pos[2])],
                                               "{} map".format(world_map.map_name), 0, 125, 0)

            maps_to_send.add(map)

        for map_to_send in maps_to_send:
            for x in range(0, map_to_send.width):
                for y in range(0, map_to_send.height):
                    self.send_map_data(map_to_send.maps[(x * y) + x])

    def send_status_holograms(self):
        for hologram in self.current_world.holograms:
            if self.status_holograms.get(hologram.server) is None:
                self.status_holograms[hologram.server] = []

            holograms = []
            pos = deepcopy(hologram.pos)

            # Move to center of block
            pos[0] += 0.5
            pos[2] += 0.5

            if self.hologram_y_offset:
                pos[1] += self.hologram_y_offset

            holograms.append(self.send_status_hologram(pos))

            self.status_holograms[hologram.server].append(holograms)

    def send_status_hologram_texts(self):
        for server, holograms in self.status_holograms.items():
            lines = self.protocol.factory.server_statuses.get(server, None)

            if self.protocol.debug_mode is True:
                lines = chat.Message("Line 1 for " + server + " server status\n\nLine 2 for " + server + " server status")

            if lines is not None:
                for hologram in holograms:
                    self.send_entity_metadata(hologram[0], self.get_status_hologram_metadata(lines))

    def send_debug_markers(self):
        spawn = self.current_world.spawn
        self.send_debug_marker([int(spawn.get('x')), int(spawn.get('y')), int(spawn.get('z'))], 'Spawn', 0, 100, 0)

        for portal in self.current_world.portals:
            for x in range(portal.pos1[0], portal.pos2[0] + 1):
                for y in range(portal.pos1[1], portal.pos2[1] + 1):
                    for z in range(portal.pos1[2], portal.pos2[2] + 1):
                        self.send_debug_marker([x, y, z], 'Portal to {}'.format(portal.destination), 0, 150, 0)

    def spawn_player(self, effects=False):
        self.send_spawn()

        if effects is True:
            self.send_spawn_effect()

    def reset_world(self, effects=False):
        if self.protocol.debug_mode:
            self.clear_debug_markers()

        self.status_holograms = dict()
        self.send_respawn()

        self.protocol.ticker.add_delay(1, self.send_world)
        self.protocol.ticker.add_delay(20, self.send_music)

        if effects is True:
            self.protocol.ticker.add_delay(2, self.send_reset_sound)

    def next_world(self):
        if len(worlds[self.chunk_format]) > 1:
            index = worlds[self.chunk_format].index(self.current_world)
            next_index = index + 1 if index < len(worlds[self.chunk_format]) - 1 else 0
            self.current_world = worlds[self.chunk_format][next_index]

        self.reset_world()

    def previous_world(self):
        if len(worlds[self.chunk_format]) > 1:
            index = worlds[self.chunk_format].index(self.current_world)
            prev_index = index - 1 if index > 0 else len(worlds[self.chunk_format]) - 1
            self.current_world = worlds[self.chunk_format][prev_index]

        self.reset_world()

    def get_data_pack(self) -> Optional[DataPack]:
        return None

    @abc.abstractmethod
    def send_join_game(self):
        raise NotImplementedError('send_join_game must be defined to use this base class')

    @abc.abstractmethod
    def send_spawn(self):
        raise NotImplementedError('send_spawn must be defined to use this base class')

    @abc.abstractmethod
    def send_spawn_effect(self):
        raise NotImplementedError('send_spawn_effect must be defined to use this base class')

    @abc.abstractmethod
    def send_respawn(self):
        raise NotImplementedError('send_respawn must be defined to use this base class')

    @abc.abstractmethod
    def send_reset_world(self):
        raise NotImplementedError('send_reset_world must be defined to use this base class')

    @abc.abstractmethod
    def send_keep_alive(self):
        raise NotImplementedError('send_keep_alive must be defined to use this base class')

    @abc.abstractmethod
    def send_time(self):
        raise NotImplementedError('send_time must be defined to use this base class')

    @abc.abstractmethod
    def send_weather(self, rain=False):
        raise NotImplementedError('send_weather must be defined to use this base class')

    @abc.abstractmethod
    def send_music(self, stop=False):
        raise NotImplementedError('send_music must be defined to use this base class')

    @abc.abstractmethod
    def send_reset_sound(self):
        raise NotImplementedError('send_reset_sound must be defined to use this base class')

    @abc.abstractmethod
    def send_commands(self):
        raise NotImplementedError('send_commands must be defined to use this base class')

    @abc.abstractmethod
    def send_chat_message(self, message: Message):
        raise NotImplementedError('send_chat_message must be defined to use this base class')

    @abc.abstractmethod
    def send_tablist(self):
        raise NotImplementedError('send_tablist must be defined to use this base class')

    @abc.abstractmethod
    def send_inventory(self):
        raise NotImplementedError('send_inventory must be defined to use this base class')

    @abc.abstractmethod
    def send_portal(self, server):
        raise NotImplementedError('send_portal must be defined to use this base class')

    @abc.abstractmethod
    def send_entity_metadata(self, entity_id: int, metadata: Dict[Tuple[int, int], Union[str, int, bool]]):
        raise NotImplementedError('send_entity_metadata must be defined to use this base class')

    @abc.abstractmethod
    def send_map_frame(self, pos: List[float], direction: Direction, map_id: int):
        raise NotImplementedError('send_map_frame must be defined to use this base class')

    @abc.abstractmethod
    def send_map_data(self, part: MapPart):
        raise NotImplementedError('send_map_data must be defined to use this base class')

    @abc.abstractmethod
    def send_status_hologram(self, pos: List[float]):
        raise NotImplementedError('send_status_hologram must be defined to use this base class')

    @staticmethod
    @abc.abstractmethod
    def get_status_hologram_metadata(text: chat.Message = None):
        raise NotImplementedError('get_status_hologram_metadata must be defined to use this base class')

    @abc.abstractmethod
    def send_debug_marker(self, pos: List[int], name: str, r: int, g: int, b: int):
        raise NotImplementedError('send_debug_marker must be defined to use this base class')

    @abc.abstractmethod
    def clear_debug_markers(self):
        raise NotImplementedError('clear_debug_markers must be defined to use this base class')