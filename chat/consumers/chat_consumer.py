import json
from typing import Optional, Dict, Tuple

from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import AbstractBaseUser

from .db_operations import get_groups_to_add, get_unread_count, get_user_by_pk, get_file_by_id, get_message_by_id, \
    save_file_message, save_text_message, mark_message_as_read, mark_message_as_read_with_authors, save_call_message
from .message_types import MessageTypes, MessageTypeMessageRead, MessageTypeFileMessage, MessageTypeTextMessage, \
    OutgoingEventMessageRead, OutgoingEventNewTextMessage, OutgoingEventNewUnreadCount, OutgoingEventMessageIdCreated, \
    OutgoingEventNewFileMessage, OutgoingEventIsTyping, OutgoingEventStoppedTyping, OutgoingEventWentOnline, \
    OutgoingEventWentOffline, OutgoingEventNewCallMessage, OutgoingEventCallMessageOffer, \
    OutgoingEventCallMessageCandidate, OutgoingEventCallMessageAnswer, OutgoingEventCallMessageReject

from .errors import ErrorTypes, ErrorDescription
from chat.models import MessageModel, UploadedFile
from chat.serializers import serialize_file_model
from django.conf import settings
import logging

logger = logging.getLogger('chat.chat_consumer')
TEXT_MAX_LENGTH = getattr(settings, 'TEXT_MAX_LENGTH', 65535)
UNAUTH_REJECT_CODE: int = 4001


class InputValidationError(Exception):
    def __init__(self, type, message):
        self.type = type
        self.message = message


class Validators:
    @staticmethod
    def validate_user_pk(data, key='user_pk'):
        if key not in data or not isinstance(data[key], str):
            raise InputValidationError(ErrorTypes.MessageParsingError, "key error")
        return data[key]

    @staticmethod
    def validate_message_random_id(data):
        if 'random_id' not in data or not isinstance(data['random_id'], str) or int(data['random_id']) > 0:
            raise InputValidationError(ErrorTypes.MessageParsingError, "'random_id' error")
        return data['random_id']

    @staticmethod
    def validate_message_id(data):
        if 'message_id' not in data or not isinstance(data['message_id'], str):
            raise InputValidationError(ErrorTypes.MessageParsingError, "'message_id' error")
        elif int(data['message_id']) <= 0:
            raise InputValidationError(ErrorTypes.InvalidMessageReadId, "'message_id' should be > 0")
        return data['message_id']

    @staticmethod
    def validate_message_text(data):
        if 'text' not in data or not isinstance(data['text'], str) \
                or str(data['text']).strip() == '' \
                or len(data['text']) > TEXT_MAX_LENGTH:
            raise InputValidationError(ErrorTypes.MessageParsingError, "'text' error")
        return data['text']

    @staticmethod
    async def validate_and_get_recipient(user_pk):
        # TODO save users to cache
        recipient: Optional[AbstractBaseUser] = await get_user_by_pk(user_pk)
        if not recipient:
            raise InputValidationError(ErrorTypes.InvalidUserPk, f"User with pk {user_pk} does not exist")
        return recipient

    @staticmethod
    def validate_call_message_type(data):
        if "type" not in data or data["type"] not in ["offer", "answer", "candidate"]:
            raise InputValidationError(ErrorTypes.MessageParsingError, "'type' error")
        return data["type"]

    @staticmethod
    def validate_call_message_offer(data):
        if "offer" not in data or not isinstance(data["offer"], dict):
            raise InputValidationError(ErrorTypes.MessageParsingError, "'offer' error")
        return data["offer"]

    @staticmethod
    def validate_call_message_answer(data):
        if "answer" not in data or not isinstance(data["answer"], dict):
            raise InputValidationError(ErrorTypes.MessageParsingError, "'answer' error")
        return data["answer"]

    @staticmethod
    def validate_call_message_candidate(data):
        if "candidate" not in data or not isinstance(data["candidate"], dict):
            raise InputValidationError(ErrorTypes.MessageParsingError, "'candidate' error")
        return data["candidate"]

    @staticmethod
    def get_optional_reason(data):
        if "reason" in data and isinstance(data["reason"], str) and len(data["reason"]) < 1024:
            return data["reason"]
        return None


def get_user_details(user):
    return {
        'id': user.pk,
        'name': user.name,
        'email': user.email,
    }


class ChatConsumer(AsyncWebsocketConsumer):
    def is_not_me(self, user_pk: str):
        return user_pk != self.group_name

    async def _after_message_save(self, msg: MessageModel, rid: int, user_pk: str):
        ev = OutgoingEventMessageIdCreated(random_id=rid, db_id=msg.id)._asdict()
        # logger.info(f"Message with id {msg.id} saved, firing events to {user_pk} & {self.group_name}")
        await self.channel_layer.group_send(user_pk, ev)
        await self.channel_layer.group_send(self.group_name, ev)
        if self.is_not_me(user_pk):
            new_unread_count = await get_unread_count(self.group_name, user_pk)
            await self.channel_layer.group_send(
                user_pk,
                OutgoingEventNewUnreadCount(
                    sender=self.group_name,
                    unread_count=new_unread_count
                )._asdict())

    async def connect(self):
        # TODO:
        # 1. Set user online
        # 2. Notify other users that the user went online
        # 3. Add the user to all groups where he has dialogs
        # Call self.scope["session"].save() on any changes to User
        if self.scope["user"] and self.scope["user"].is_authenticated:
            self.user: AbstractBaseUser = self.scope['user']
            self.group_name: str = str(self.user.pk)
            self.sender_name: str = self.user.name
            logger.info(f"User {self.user.pk} connected, adding {self.channel_name} to {self.group_name}")
            await self.channel_layer.group_add(self.group_name, self.channel_name)
            await self.accept()
            dialogs = await get_groups_to_add(self.user)
            logger.info(f"User {self.user.pk} connected, sending 'user_went_online' to {dialogs} dialog groups")
            for d in dialogs:  # type: int
                if str(d) != self.group_name:
                    await self.channel_layer.group_send(
                        str(d),
                        OutgoingEventWentOnline(
                            user_pk=str(self.user.pk)
                        )._asdict()
                    )
        else:
            logger.info(f"Rejecting unauthenticated user with code {UNAUTH_REJECT_CODE}")
            await self.close(code=UNAUTH_REJECT_CODE)

    async def disconnect(self, close_code):
        # TODO:
        # Set user offline
        # Save user was_online
        # Notify other users that the user went offline
        if close_code != UNAUTH_REJECT_CODE and getattr(self, 'user', None) is not None:
            logger.info(
                f"User {self.user.pk} disconnected, removing channel {self.channel_name} from group {self.group_name}")
            await self.channel_layer.group_discard(self.group_name, self.channel_name)
            dialogs = await get_groups_to_add(self.user)
            logger.info(f"User {self.user.pk} disconnected, sending 'user_went_offline' to {dialogs} dialog groups")
            for d in dialogs:
                await self.channel_layer.group_send(
                    str(d),
                    OutgoingEventWentOffline(
                        user_pk=str(self.user.pk)
                    )._asdict()
                )

    # -----------------------------------------
    async def handle_is_typing(self, data: Dict[str, str]):
        dialogs = await get_groups_to_add(self.user)
        logger.info(f"User {self.user.pk} is typing, sending 'is_typing' to {dialogs} dialog groups")
        for d in dialogs:
            if str(d) != self.group_name:
                is_typing = data.get('typing', True)
                await self.channel_layer.group_send(
                    str(d),
                    OutgoingEventIsTyping(
                        user_pk=str(self.user.pk),
                        typing=is_typing
                    )._asdict()
                )

    async def handle_typing_stopped(self, data: Dict[str, str]):
        # dialogs = await get_groups_to_add(self.user)
        # logger.info(
        #     f"User {self.user.pk} has stopped typing, sending 'stopped_typing' to {dialogs} dialog groups")
        # for d in dialogs:
        #     if str(d) != self.group_name:
        #         await self.channel_layer.group_send(
        #             str(d),
        #             OutgoingEventStoppedTyping(
        #                 user_pk=str(self.user.pk)
        #             )._asdict()
        #         )
        pass

    async def handle_message_read(self, data: Dict[str, str]):
        user_pk = Validators.validate_user_pk(data)
        mid = Validators.validate_message_id(data)
        if self.is_not_me(user_pk):
            await self.channel_layer.group_send(
                user_pk,
                OutgoingEventMessageRead(
                    message_id=mid,
                    sender=user_pk,
                    receiver=self.group_name
                )._asdict()
            )

        # TODO we should send one read event to read all messages and not bunch of events
        # TODO we may save frequently used users in cache
        # TODO do we need validation here ?
        await mark_message_as_read_with_authors(self.group_name, user_pk, mid)

        if self.is_not_me(user_pk):
            new_unread_count = await get_unread_count(user_pk, self.group_name)
            await self.channel_layer.group_send(
                self.group_name,
                OutgoingEventNewUnreadCount(
                    sender=user_pk,
                    unread_count=new_unread_count
                )._asdict()
            )

    async def handle_file_message(self, data: Dict[str, str]):
        # if 'file_id' not in data or data['file_id'] == '':
        #     return ErrorTypes.MessageParsingError, "'file_id' error"
        # elif 'user_pk' not in data or not isinstance(data['user_pk'], str):
        #     return ErrorTypes.MessageParsingError, "'user_pk' error"
        # elif 'random_id' not in data or not isinstance(data['random_id'], str) or int(data['random_id']) > 0:
        #     return ErrorTypes.MessageParsingError, "'random_id' error"
        # elif not isinstance(data['file_id'], str):
        #     return ErrorTypes.FileMessageInvalid, "'file_id' should be a string"
        # else:
        #     file_id = data['file_id']
        #     user_pk = data['user_pk']
        #     rid = data['random_id']
        #     # We can't send the message right away like in the case with text message
        #     # because we don't have the file url.
        #     file: Optional[UploadedFile] = await get_file_by_id(file_id)
        #     logger.info(f"DB check if file {file_id} exists resulted in {file}")
        #     if not file:
        #         return ErrorTypes.FileDoesNotExist, f"File with id {file_id} does not exist"
        #
        #     recipient: Optional[AbstractBaseUser] = await get_user_by_pk(user_pk)
        #     logger.info(f"DB check if user {user_pk} exists resulted in {recipient}")
        #     if not recipient:
        #         return ErrorTypes.InvalidUserPk, f"User with pk {user_pk} does not exist"
        #     else:
        #         logger.info(f"Will save file message from {self.user} to {recipient}")
        #         msg = await save_file_message(file, from_=self.user, to=recipient)
        #         await self._after_message_save(msg, rid=rid, user_pk=user_pk)
        #         logger.info(f"Sending file message for file {file_id} from {self.user} to {recipient}")
        #         # We don't need to send random_id here because we've already saved the file to db
        #
        #         await self.channel_layer.group_send(
        #             user_pk,
        #             OutgoingEventNewFileMessage(
        #                 db_id=msg.id,
        #                 file=serialize_file_model(
        #                     file),
        #                 sender=self.group_name,
        #                 receiver=user_pk,
        #                 sender_name=self.sender_name
        #             )._asdict()
        #         )
        pass

    async def handle_text_message(self, data: Dict[str, str]):
        data: MessageTypeTextMessage
        user_pk = Validators.validate_user_pk(data)
        text = Validators.validate_message_text(data)
        rid = Validators.validate_message_random_id(data)
        # first we send data to channel layer to not perform any synchronous operations,
        # and only after we do sync DB stuff
        # We need to create a 'random id' - a temporary id for the message, which is not yet
        # saved to the database. I.e. for the client it is 'pending delivery' and can be
        # considered delivered only when it's saved to database and received a proper id,
        # which is then broadcast separately both to sender & receiver.
        # logger.info(f"Validation passed, sending text message from {self.group_name} to {user_pk}")
        if self.is_not_me(user_pk):
            await self.channel_layer.group_send(user_pk, OutgoingEventNewTextMessage(
                random_id=rid,
                text=text,
                sender=self.group_name,
                receiver=user_pk,
                sender_name=self.sender_name
            )._asdict())

        # logger.info(f"DB check if user {user_pk} exists resulted in {recipient}")
        # TODO save users to cache
        recipient: Optional[AbstractBaseUser] = await get_user_by_pk(user_pk)
        if not recipient:
            return ErrorTypes.InvalidUserPk, f"User with pk {user_pk} does not exist"

        # logger.info(f"Will save text message from {self.user} to {recipient}")
        msg = await save_text_message(text, from_=self.user, to=recipient)
        await self._after_message_save(msg, rid=rid, user_pk=user_pk)

    async def handle_call_message(self, data: Dict[str, str]):
        user_pk = Validators.validate_user_pk(data)
        rid = Validators.validate_message_random_id(data)
        if not self.is_not_me(user_pk):
            # do nothing
            return

        await self.channel_layer.group_send(user_pk, OutgoingEventNewCallMessage(
            random_id=rid,
            sender=self.group_name,
            receiver=user_pk,
            sender_name=self.sender_name
        )._asdict())

        recipient = await Validators.validate_and_get_recipient(user_pk)
        msg = await save_call_message(from_=self.user, to=recipient)
        await self._after_message_save(msg, rid=rid, user_pk=user_pk)

    async def handle_call_message_offer(self, data: Dict[str, str]):
        # main is 26
        # other is 37
        user_pk = Validators.validate_user_pk(data)
        if user_pk == self.group_name:
            return

        offer = Validators.validate_call_message_offer(data)
        await self.channel_layer.group_send(user_pk, OutgoingEventCallMessageOffer(
            offer=offer,
            from_user=get_user_details(self.user)
        )._asdict())

    async def handle_call_message_answer(self, data: Dict[str, str]):
        # main is 26
        # other is 37
        user_pk = Validators.validate_user_pk(data)
        if user_pk == self.group_name:
            return

        answer = Validators.validate_call_message_answer(data)
        await self.channel_layer.group_send(user_pk, OutgoingEventCallMessageAnswer(
            answer=answer,
            from_user=get_user_details(self.user)
        )._asdict())

    async def handle_call_message_candidate(self, data: Dict[str, str]):
        user_pk = Validators.validate_user_pk(data)
        if user_pk == self.group_name:
            return

        candidate = Validators.validate_call_message_candidate(data)
        await self.channel_layer.group_send(user_pk, OutgoingEventCallMessageCandidate(
            candidate=candidate,
            from_user=get_user_details(self.user)
        )._asdict())

    async def handle_call_message_reject(self, data: Dict[str, str]):
        from_user_id = Validators.validate_user_pk(data, 'from_user_id')
        if from_user_id == self.group_name:
            return
        reason = Validators.get_optional_reason(data)
        await self.channel_layer.group_send(from_user_id, OutgoingEventCallMessageReject(
            from_user=get_user_details(self.user),
            reason=reason,
        )._asdict())
    # -----------------------------------------

    async def handle_received_message(self, msg_type: MessageTypes, data: Dict[str, str]) -> Optional[ErrorDescription]:
        # TODO whenever we execute this function, we should check if self.user has dialog opened with user_pk
        logger.info(f"Received message type {msg_type.name} from user {self.group_name} with data {data}")
        if msg_type == MessageTypes.WentOffline \
                or msg_type == MessageTypes.WentOnline \
                or msg_type == MessageTypes.MessageIdCreated \
                or msg_type == MessageTypes.ErrorOccurred:
            logger.info(f"Ignoring message {msg_type.name}")
            return

        try:
            handlers = {
                MessageTypes.IsTyping: self.handle_is_typing,
                MessageTypes.TypingStopped: self.handle_typing_stopped,
                MessageTypes.MessageRead: self.handle_message_read,
                MessageTypes.FileMessage: self.handle_file_message,
                MessageTypes.TextMessage: self.handle_text_message,
                MessageTypes.CallMessage: self.handle_call_message,
                MessageTypes.CallMessageOffer: self.handle_call_message_offer,
                MessageTypes.CallMessageAnswer: self.handle_call_message_answer,
                MessageTypes.CallMessageCandidate: self.handle_call_message_candidate,
                MessageTypes.CallMessageReject: self.handle_call_message_reject,
            }
            if msg_type in handlers:
                return await handlers[msg_type](data)
            else:
                return ErrorTypes.MessageParsingError, f"Unknown message type {msg_type.name}"
        except InputValidationError as e:
            print(e)
            return e.type, e.message

    # Receive message from WebSocket
    async def receive(self, text_data=None, bytes_data=None):
        logger.info(f"Receive fired")
        error: Optional[ErrorDescription] = None
        try:
            text_data_json = json.loads(text_data)
            logger.info(f"From {self.group_name} received '{text_data_json}")
            if not ('msg_type' in text_data_json):
                error = (ErrorTypes.MessageParsingError, "msg_type not present in json")
            else:
                msg_type = text_data_json['msg_type']
                if not isinstance(msg_type, int):
                    error = (ErrorTypes.MessageParsingError, "msg_type is not an int")
                else:
                    try:
                        msg_type_case: MessageTypes = MessageTypes(msg_type)
                        error = await self.handle_received_message(msg_type_case, text_data_json)
                    except ValueError as e:
                        error = (ErrorTypes.MessageParsingError, f"msg_type decoding error - {e}")
        except json.JSONDecodeError as e:
            error = (ErrorTypes.MessageParsingError, f"jsonDecodeError - {e}")
        if error is not None:
            error_data = {
                'msg_type': MessageTypes.ErrorOccurred,
                'error': error
            }
            logger.info(f"Will send error {error_data} to {self.group_name}")
            await self.send(text_data=json.dumps(error_data))

    async def new_unread_count(self, event: dict):
        await self.send(text_data=OutgoingEventNewUnreadCount(**event).to_json())

    async def message_read(self, event: dict):
        await self.send(text_data=OutgoingEventMessageRead(**event).to_json())

    async def message_id_created(self, event: dict):
        await self.send(text_data=OutgoingEventMessageIdCreated(**event).to_json())

    async def new_text_message(self, event: dict):
        await self.send(text_data=OutgoingEventNewTextMessage(**event).to_json())

    async def new_call_message(self, event: dict):
        await self.send(text_data=OutgoingEventNewCallMessage(**event).to_json())

    async def new_call_message_offer(self, event: dict):
        await self.send(text_data=OutgoingEventCallMessageOffer(**event).to_json())

    async def new_call_message_answer(self, event: dict):
        await self.send(text_data=OutgoingEventCallMessageAnswer(**event).to_json())

    async def new_call_message_candidate(self, event: dict):
        await self.send(text_data=OutgoingEventCallMessageCandidate(**event).to_json())

    async def new_call_message_reject(self, event: dict):
        await self.send(text_data=OutgoingEventCallMessageReject(**event).to_json())

    async def new_file_message(self, event: dict):
        await self.send(text_data=OutgoingEventNewFileMessage(**event).to_json())

    async def is_typing(self, event: dict):
        await self.send(text_data=OutgoingEventIsTyping(**event).to_json())

    async def stopped_typing(self, event: dict):
        await self.send(text_data=OutgoingEventStoppedTyping(**event).to_json())

    async def user_went_online(self, event):
        await self.send(text_data=OutgoingEventWentOnline(**event).to_json())

    async def user_went_offline(self, event):
        await self.send(text_data=OutgoingEventWentOffline(**event).to_json())
