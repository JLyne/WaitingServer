from quarry.types.chat import Message

from waitingserver.versions import Version_1_19


class Version_1_19_1(Version_1_19):
    protocol_version = 760

    def send_chat_message(self, message: Message):
        self.protocol.send_packet('system_message',
                                  self.protocol.buff_type.pack_chat(message),
                                  self.protocol.buff_type.pack("?", False))  # Not an overlay (action bar) message

