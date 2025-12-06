from waitingserver.protocol import Protocol
from waitingserver.versions import Version_1_21_6


class Version_1_21_7(Version_1_21_6):
    protocol_version = 772
    chunk_format = '1.21.7'

    def __init__(self, protocol: Protocol, bedrock: bool = False):
        super().__init__(protocol, bedrock)
