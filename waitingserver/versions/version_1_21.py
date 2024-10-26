from waitingserver.protocol import Protocol
from waitingserver.versions import Version_1_20_5


class Version_1_21(Version_1_20_5):
    protocol_version = 767
    chunk_format = '1.21'

    def __init__(self, protocol: Protocol, bedrock: False):
        super(Version_1_21, self).__init__(protocol, bedrock)
