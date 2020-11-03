from versions import Version

from waitingserver import Protocol

class Version_1_15(Version):
    def __init__(self, protocol: Protocol, bedrock: False):
        super(Version_1_15, self).__init__(protocol, bedrock)
        self.version_name = '1.15'

    def send_join_game(self):
        self.protocol.send_packet("join_game",
                         self.protocol.buff_type.pack("iBqiB", 0, 1, 0, 0, 0),
                         self.protocol.buff_type.pack_string("default"),
                         self.protocol.buff_type.pack_varint(16),
                         self.protocol.buff_type.pack("??", False, True))

    def send_respawn(self):
        self.protocol.send_packet("respawn", self.protocol.buff_type.pack("iBq", 1, 0, 1), self.protocol.buff_type.pack_string("default"))
        self.protocol.send_packet("respawn", self.protocol.buff_type.pack("iBq", 0, 0, 1), self.protocol.buff_type.pack_string("default"))