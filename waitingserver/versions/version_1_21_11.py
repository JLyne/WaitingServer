from copy import deepcopy

from quarry.data.data_packs import vanilla_data_packs, pack_formats
from quarry.types.data_pack import DataPack
from quarry.types.namespaced_key import NamespacedKey
from quarry.types.nbt import TagInt, TagByte, TagCompound

from waitingserver.protocol import Protocol
from waitingserver.versions import Version_1_21_9


class Version_1_21_11(Version_1_21_9):
    protocol_version = 1073742109
    chunk_format = '1.21.11'

    hologram_entity_id = 131  # Text display
    map_entity_id = 60  # Glow item frame
    map_item_id = 1104  # Filled map


    def __init__(self, protocol: Protocol, bedrock: bool = False):
        super().__init__(protocol, bedrock)

    def get_data_pack(self):
        if self.data_pack:
            return self.data_pack

        vanilla_pack = vanilla_data_packs[self.protocol_version]

        # Remove void overrides
        void = deepcopy(vanilla_pack.contents[NamespacedKey.minecraft('worldgen/biome')]
                        .get(NamespacedKey.minecraft('the_void')))

        void['attributes'] = {}
        void['effects'] = {
            'water_color': '#ffffff'
        }

        contents = {
            NamespacedKey.minecraft('dimension_type'): {
                NamespacedKey.minecraft('overworld'): self.get_dimension_settings('overworld'),
                NamespacedKey.minecraft('the_nether'): self.get_dimension_settings('the_nether'),
                NamespacedKey.minecraft('the_end'): self.get_dimension_settings('the_end'),
                NamespacedKey.minecraft('void'): self.get_dimension_settings('void'),
            },
            NamespacedKey.minecraft('worldgen/biome'): {
                NamespacedKey.minecraft('the_void'): void
            }
        }

        self.data_pack = DataPack(NamespacedKey("rtgame", "waitingserver"), "1.0", pack_formats[self.protocol_version], contents)
        return self.data_pack

    def get_dimension_settings(self, name: str):
        vanilla_pack = vanilla_data_packs[self.protocol_version]

        if name == 'void':
            settings = deepcopy(vanilla_pack.contents[NamespacedKey.minecraft('dimension_type')]
                        .get(NamespacedKey.minecraft('overworld')))

            settings['has_ceiling'] = 1
            settings['has_skylight'] = 0
            settings['attributes'] = {
                'minecraft:visual/sun_angle': 180,
                'minecraft:visual/moon_angle': 180,
            }
            del settings['timelines']
        else:
            settings = deepcopy(vanilla_pack.contents[NamespacedKey.minecraft('dimension_type')]
                                .get(NamespacedKey.minecraft(name)))

        settings['height'] = TagInt(384)
        settings['logical_height'] = TagInt(384)
        settings['min_y'] = TagInt(-64)
        settings['attributes']['minecraft:audio/background_music'] = {}
        settings['attributes']['minecraft:audio/ambient_sounds'] = {}

        return settings
