from quarry.types.namespaced_key import NamespacedKey

from waitingserver.protocol import Protocol
from waitingserver.versions import Version_1_21_11


class Version_26_1(Version_1_21_11):
    protocol_version = 1073742127
    chunk_format = '26.1'

    def __init__(self, protocol: Protocol, bedrock: bool = False):
        super().__init__(protocol, bedrock)

    def send_time(self):
        dimension_registry = self.protocol.data_packs.get_registry(NamespacedKey.minecraft('dimension_type'))
        clock_registry = self.protocol.data_packs.get_registry(NamespacedKey.minecraft('world_clock'))
        dimension = dimension_registry.get(self.current_world.dimension)
        clock = dimension['default_clock'] # Default clock for current dimension type

        if clock is None:
            return

        id = list(clock_registry).index(NamespacedKey.from_string(clock))

        self.protocol.send_packet('set_time',
                                  self.protocol.buff_type.pack("Q", 0) + # Game time
                                  self.protocol.buff_type.pack_varint(1) + # Number of clocks in map
                                  self.protocol.buff_type.pack_varint(id) + # Id of clock
                                  self.protocol.buff_type.pack_varint(self.current_world.time, 64) + # World time (varlong)
                                  self.protocol.buff_type.pack("ff", 0, 1 if self.current_world.cycle else 0)) # "Partial ticks"?, rate

    def get_dimension_settings(self, name: str):
        settings = super().get_dimension_settings(name)

        if name == 'void':
            settings['attributes']['minecraft:visual/ambient_light_color'] = 0

        return settings