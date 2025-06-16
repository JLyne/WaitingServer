import hmac

from quarry.types.chat import Message
from quarry.types.uuid import UUID


def entry_component(current, total):
    return Message({
            "text": '\n\n\nEntry ',
            "bold": True,
            "color": "gold",
            "extra": [
                {
                    "text": "#",
                    "bold": False,
                },
                {
                    "text": '{}/{}'.format(current, total),
                    "bold": True,
                }
            ]
        })


def entry_navigation_component(uuid: UUID, secret):
    from waitingserver.config import voting_url

    token = hmac.new(key=str.encode(secret), msg=uuid.to_bytes(), digestmod="sha256")
    url = voting_url.format(uuid=uuid.to_hex(False), token=token.hexdigest())

    return Message({
            "text": "\n",
            "color": "gold",
            "extra": [
                {
                    "text": "[Prev Entry]",
                    "bold": True,
                    "clickEvent": {
                        "action": "run_command",
                        "value": "/prev"
                    },
                    "click_event": {
                        "action": "run_command",
                        "command": "/prev"
                    },
                },
                {
                    "text": " ",
                },
                {
                    "text": "[Next Entry]",
                    "bold": True,
                    "clickEvent": {
                        "action": "run_command",
                        "value": "/next"
                    },
                    "click_event": {
                        "action": "run_command",
                        "command": "/next"
                    }
                },
                {
                    "text": "\n\n"
                },
                {
                    "text": "[Cast your Votes]",
                    "bold": True,
                    "color": "aqua",
                    "clickEvent": {
                        "action": "open_url",
                        "value": url
                    },
                    "click_event": {
                        "action": "open_url",
                        "url": url
                    }
                },
                {
                    "text": "\n\n"
                }
            ]
        })
