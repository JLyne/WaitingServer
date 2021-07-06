from versions import Version_1_17
from waitingserver import Protocol


class Version_1_17_1(Version_1_17):
    def __init__(self, protocol: Protocol, bedrock: False):
        super(Version_1_17_1, self).__init__(protocol, bedrock)

    def send_inventory(self):
        data = [
            self.protocol.buff_type.pack('B', 0),
            self.protocol.buff_type.pack_varint(0),
            self.protocol.buff_type.pack_varint(46)
        ]

        for i in range(0, 46):
            data.append(self.protocol.buff_type.pack('?', False))

        data.append(self.protocol.buff_type.pack('?', False))
        self.protocol.send_packet('window_items', *data)

