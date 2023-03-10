import enum
import json

# TODO: add tx_id to distinguish errors for different transactions
from typing import NamedTuple, Optional, Dict

try:
    from typing import TypedDict
except ImportError:
    TypedDict = dict


class MessageTypeTextMessage(TypedDict):
    text: str
    user_pk: str
    random_id: int


class MessageTypeMessageRead(TypedDict):
    user_pk: str
    message_id: int


class MessageTypeFileMessage(TypedDict):
    file_id: str
    user_pk: str
    random_id: int


class MessageTypes(enum.IntEnum):
    WentOnline = 1
    WentOffline = 2
    TextMessage = 3
    FileMessage = 4
    IsTyping = 5
    MessageRead = 6
    ErrorOccurred = 7
    MessageIdCreated = 8
    NewUnreadCount = 9
    TypingStopped = 10
    CallMessage = 11
    CallMessageOffer = 12
    CallMessageAnswer = 13
    CallMessageCandidate = 14
    CallMessageReject = 15


class UserMessageTypes(enum.Enum):
    Text = "text"
    Call = "call"
    File = "file"


# class OutgoingEventBase(TypedDict):
#

class OutgoingEventMessageRead(NamedTuple):
    message_id: int
    sender: str
    receiver: str
    type: str = "message_read"

    def to_json(self) -> str:
        return json.dumps({
            "msg_type": MessageTypes.MessageRead,
            "message_id": self.message_id,
            "sender": self.sender,
            "receiver": self.receiver
        })


class OutgoingEventNewTextMessage(NamedTuple):
    random_id: int
    text: str
    sender: str
    receiver: str
    sender_name: str
    type: str = "new_text_message"

    def to_json(self) -> str:
        return json.dumps({
            "msg_type": MessageTypes.TextMessage,
            "random_id": self.random_id,
            "text": self.text,
            "sender": self.sender,
            "receiver": self.receiver,
            "sender_name": self.sender_name,
        })


class OutgoingEventNewCallMessage(NamedTuple):
    random_id: int
    sender: str
    receiver: str
    sender_name: str
    type: str = "new_call_message"

    def to_json(self) -> str:
        return json.dumps({
            "msg_type": MessageTypes.CallMessage,
            "random_id": self.random_id,
            "text": "",
            "is_call": True,
            "sender": self.sender,
            "receiver": self.receiver,
            "sender_name": self.sender_name,
        })


class OutgoingEventCallMessageOffer(NamedTuple):
    offer: str
    from_user: dict
    type: str = "new_call_message_offer"

    def to_json(self) -> str:
        return json.dumps({
            "msg_type": MessageTypes.CallMessageOffer,
            "type": "offer",
            "offer": self.offer,
            "from_user": self.from_user,
        })


class OutgoingEventCallMessageCandidate(NamedTuple):
    candidate: str
    from_user: dict
    type: str = "new_call_message_candidate"

    def to_json(self) -> str:
        return json.dumps({
            "msg_type": MessageTypes.CallMessageCandidate,
            "type": "candidate",
            "candidate": self.candidate,
            "from_user": self.from_user,
        })


class OutgoingEventCallMessageAnswer(NamedTuple):
    answer: str
    from_user: dict
    type: str = "new_call_message_answer"

    def to_json(self) -> str:
        return json.dumps({
            "msg_type": MessageTypes.CallMessageAnswer,
            "type": "answer",
            "answer": self.answer,
            "from_user": self.from_user,
        })


class OutgoingEventCallMessageReject(NamedTuple):
    from_user: dict
    reason: Optional[str]
    type: str = "new_call_message_reject"

    def to_json(self) -> str:
        return json.dumps({
            "msg_type": MessageTypes.CallMessageReject,
            "reason": self.reason,
            "from_user": self.from_user,
        })


class OutgoingEventNewFileMessage(NamedTuple):
    db_id: int
    file: Dict[str, str]
    sender: str
    receiver: str
    sender_name: str
    type: str = "new_file_message"

    def to_json(self) -> str:
        return json.dumps({
            "msg_type": MessageTypes.FileMessage,
            "db_id": self.db_id,
            "file": self.file,
            "sender": self.sender,
            "receiver": self.receiver,
            "sender_name": self.sender_name,
        })


class OutgoingEventNewUnreadCount(NamedTuple):
    sender: str
    unread_count: int
    type: str = "new_unread_count"

    def to_json(self) -> str:
        return json.dumps({
            "msg_type": MessageTypes.NewUnreadCount,
            "sender": self.sender,
            "unread_count": self.unread_count,
        })


class OutgoingEventMessageIdCreated(NamedTuple):
    random_id: int
    db_id: int
    type: str = "message_id_created"

    def to_json(self) -> str:
        return json.dumps({
            "msg_type": MessageTypes.MessageIdCreated,
            "random_id": self.random_id,
            "db_id": self.db_id,
        })


class OutgoingEventIsTyping(NamedTuple):
    user_pk: str
    typing: bool
    type: str = "is_typing"

    def to_json(self) -> str:
        return json.dumps({
            "msg_type": MessageTypes.IsTyping,
            "user_pk": self.user_pk,
            "typing": self.typing,
        })


class OutgoingEventStoppedTyping(NamedTuple):
    user_pk: str
    type: str = "stopped_typing"

    def to_json(self) -> str:
        return json.dumps({
            "msg_type": MessageTypes.TypingStopped,
            "user_pk": self.user_pk
        })


class OutgoingEventWentOnline(NamedTuple):
    user_pk: str
    type: str = "user_went_online"

    def to_json(self) -> str:
        return json.dumps({
            "msg_type": MessageTypes.WentOnline,
            "user_pk": self.user_pk
        })


class OutgoingEventWentOffline(NamedTuple):
    user_pk: str
    type: str = "user_went_offline"

    def to_json(self) -> str:
        return json.dumps({
            "msg_type": MessageTypes.WentOffline,
            "user_pk": self.user_pk
        })
