from copy import deepcopy

from quarry.data.data_packs import vanilla_data_packs
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

    def get_dimension_settings(self, name: str):
        vanilla_pack = vanilla_data_packs[self.protocol_version]
        settings = deepcopy(vanilla_pack.contents[NamespacedKey.minecraft('dimension_type')]
                        .get(NamespacedKey.minecraft(name)))

        settings['has_ceiling'] = TagByte(0)
        settings['has_skylight'] = TagByte(1)
        settings['height'] = TagInt(384)
        settings['logical_height'] = TagInt(384)
        settings['min_y'] = TagInt(-64)
        settings['attributes']['minecraft:audio/background_music'] = TagCompound({})
        settings['attributes']['minecraft:audio/ambient_sounds'] = TagCompound({})

        return settings
