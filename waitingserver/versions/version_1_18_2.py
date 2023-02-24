from quarry.types.nbt import TagString

from waitingserver.versions import Version_1_18


class Version_1_18_2(Version_1_18):
    protocol_version = 758

    def get_dimension_settings(self, name: str):
        settings = super().get_dimension_settings(name)

        settings['infiniburn'] = TagString("#minecraft:infiniburn_{}".format(name))

        return settings

