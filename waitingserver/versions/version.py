import abc
import os
import time
from pathlib import Path

from quarry.types.buffer import Buffer

from waitingserver.protocol import Protocol
from waitingserver.config import get_default_world

parent_folder = Path(__file__).parent.parent


class Version(object, metaclass=abc.ABCMeta):
    protocol_version = None
    chunk_format = None
    tag_format = None

    tag_packet = None

    def __init__(self, protocol: Protocol, bedrock: False):
        self.protocol = protocol

        self.current_world = None

        self.last_portal = 0
        self.last_command = 0

        self.is_bedrock = bedrock

    def player_joined(self):
        self.protocol.ticker.add_loop(100, self.send_keep_alive)  # Keep alive packets
        self.protocol.ticker.add_loop(200, lambda: self.send_music(True))

        self.current_world = get_default_world(self.chunk_format)

        self.send_join_game()
        self.send_commands()
        self.send_tags()
        self.send_world()

        if self.is_bedrock:  # Prevent geyser persisting previous server inventory
            self.send_inventory()

        self.protocol.ticker.add_delay(10, self.send_tablist)
        self.protocol.ticker.add_delay(20, self.send_music)

    def packet_player_position(self, buff):
        x = buff.unpack('d')
        y = buff.unpack('d')
        z = buff.unpack('d')

        buff.unpack('b')  # on_ground

        self.check_portals(x, y, z)
        self.check_bounds(x, y, z)

    def packet_player_position_and_look(self, buff):
        x = buff.unpack('d')
        y = buff.unpack('d')
        z = buff.unpack('d')

        buff.unpack('f')  # yaw
        buff.unpack('f')  # pitch
        buff.unpack('b')  # on_ground

        self.check_portals(x, y, z)
        self.check_bounds(x, y, z)

    # Handle /spawn and /reset commands
    def packet_chat_message(self, buff):
        message = buff.unpack_string()
        now = time.time()

        if message == "/spawn" or message == "/hub":
            if now - self.last_command < 0.5:
                return

            self.spawn_player(True)
        elif message == "/reset":
            if now - self.last_command < 2:
                return

            self.reset_world()
        else:
            return

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
        self.spawn_player()

        # Clear geyser chunk cache from previous server
        if self.is_bedrock:
            self.send_reset_world()

        # Chunk packets
        for packet in self.current_world.packets:
            self.protocol.send_packet(packet.get('type'), packet.get('packet'))

        # Start/stop rain as necessary
        self.send_weather(self.current_world.weather == 'rain')

        if self.is_bedrock:  # Current versions of geyser seem to ignore the time sometimes. Send repeatedly for now.
            self.protocol.ticker.add_loop(100, self.send_time)
        else:
            self.send_time()

    def spawn_player(self, effects=False):
        self.send_spawn()

        if effects is True:
            self.send_spawn_effect()

    def reset_world(self):
        self.send_respawn()

        self.protocol.ticker.add_delay(1, self.send_world)
        self.protocol.ticker.add_delay(2, self.send_reset_sound)
        self.protocol.ticker.add_delay(20, self.send_music)

    def send_tags(self):
        tag_packet = self.__class__.get_tag_packet()

        if tag_packet is not None:
            self.protocol.send_packet("tags", tag_packet)

    @classmethod
    def get_tag_packet(cls):
        if cls.tag_packet is None:
            cls.tag_packet = Buffer(open(os.path.join(parent_folder, 'tags', cls.tag_format + '.bin'),
                             'rb').read()).read() if cls.tag_format is not None else None

        return cls.tag_packet

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
    def send_chat_message(self, message):
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
