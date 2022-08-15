from waitingserver.versions import Version_1_19


class Version_1_19_1(Version_1_19):
    protocol_version = 760

    def send_chat_message(self, message):
        self.protocol.send_packet('system_message',
                                  self.protocol.buff_type.pack_string(message),
                                  self.protocol.buff_type.pack("?", False))  # Not an overlay (action bar) message

