import json
from typing import Optional, Dict, Tuple

from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import AbstractBaseUser

from .db_operations import get_groups_to_add, get_unread_count, get_user_by_pk, get_file_by_id, get_message_by_id, \
    save_file_message, save_text_message, mark_message_as_read
from .message_types import MessageTypes, MessageTypeMessageRead, MessageTypeFileMessage, MessageTypeTextMessage, \
    OutgoingEventMessageRead, OutgoingEventNewTextMessage, OutgoingEventNewUnreadCount, OutgoingEventMessageIdCreated, \
    OutgoingEventNewFileMessage, OutgoingEventIsTyping, OutgoingEventStoppedTyping, OutgoingEventWentOnline, \
    OutgoingEventWentOffline

from .errors import ErrorTypes, ErrorDescription
from chat.models import MessageModel, UploadedFile
from chat.serializers import serialize_file_model
from django.conf import settings
import logging

logger = logging.getLogger('chat.chat_consumer')
TEXT_MAX_LENGTH = getattr(settings, 'TEXT_MAX_LENGTH', 65535)
UNAUTH_REJECT_CODE: int = 4001


class ChatConsumer(AsyncWebsocketConsumer):
    async def _after_message_save(self, msg: MessageModel, rid: int, user_pk: str):
        ev = OutgoingEventMessageIdCreated(random_id=rid, db_id=msg.id)._asdict()
        logger.info(f"Message with id {msg.id} saved, firing events to {user_pk} & {self.group_name}")
        await self.channel_layer.group_send(user_pk, ev)
        await self.channel_layer.group_send(self.group_name, ev)
        if user_pk != self.group_name:
            new_unreads = await get_unread_count(self.group_name, user_pk)
            await self.channel_layer.group_send(
                user_pk,
                OutgoingEventNewUnreadCount(
                    sender=self.group_name,
                    unread_count=new_unreads
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
            self.sender_username: str = self.user.get_username()
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
        if 'user_pk' not in data or not isinstance(data['user_pk'], str):
            return ErrorTypes.MessageParsingError, "'user_pk' error"
        elif 'message_id' not in data or not isinstance(data['message_id'], str):
            return ErrorTypes.MessageParsingError, "'message_id' error"
        elif int(data['message_id']) <= 0:
            return ErrorTypes.InvalidMessageReadId, "'message_id' should be > 0"
        # elif data['user_pk'] == self.group_name:
        #     return ErrorTypes.InvalidUserPk, "'user_pk' can't be self  (you can't mark self messages as read)"
        user_pk = data['user_pk']
        mid = data['message_id']
        logger.info(f"Validation passed, marking msg from {user_pk} to {self.group_name} with id {mid} as read")

        # send event if we are not sending message to ourselves
        if user_pk != self.group_name:
            await self.channel_layer.group_send(
                user_pk,
                OutgoingEventMessageRead(
                    message_id=mid,
                    sender=user_pk,
                    receiver=self.group_name
                )._asdict()
            )

        recipient: Optional[AbstractBaseUser] = await get_user_by_pk(user_pk)
        logger.info(f"DB check if user {user_pk} exists resulted in {recipient}")
        if not recipient:
            return ErrorTypes.InvalidUserPk, f"User with pk {user_pk} does not exist"

        msg_res: Optional[Tuple[str, str]] = await get_message_by_id(mid)
        if not msg_res or (msg_res[0] != self.group_name or msg_res[1] != user_pk):
            return ErrorTypes.InvalidMessageReadId, f"Message error"

        await mark_message_as_read(mid)
        if user_pk != self.group_name:
            new_unreads = await get_unread_count(user_pk, self.group_name)
            await self.channel_layer.group_send(
                self.group_name,
                OutgoingEventNewUnreadCount(
                    sender=user_pk,
                    unread_count=new_unreads
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
        #                 sender_username=self.sender_username
        #             )._asdict()
        #         )
        pass

    async def handle_text_message(self, data: Dict[str, str]):
        data: MessageTypeTextMessage
        if 'text' not in data or not isinstance(data['text'], str) \
                or str(data['text']).strip() == '' \
                or len(data['text']) > TEXT_MAX_LENGTH:
            return ErrorTypes.MessageParsingError, "'text' error"
        elif 'user_pk' not in data or not isinstance(data['user_pk'], str):
            return ErrorTypes.MessageParsingError, "'user_pk' error"
        elif 'random_id' not in data or not isinstance(data['random_id'], str) or int(data['random_id']) > 0:
            return ErrorTypes.MessageParsingError, "'random_id' error"

        text = data['text']
        user_pk = data['user_pk']
        rid = data['random_id']
        # first we send data to channel layer to not perform any synchronous operations,
        # and only after we do sync DB stuff
        # We need to create a 'random id' - a temporary id for the message, which is not yet
        # saved to the database. I.e. for the client it is 'pending delivery' and can be
        # considered delivered only when it's saved to database and received a proper id,
        # which is then broadcast separately both to sender & receiver.
        logger.info(f"Validation passed, sending text message from {self.group_name} to {user_pk}")
        if user_pk != self.group_name:
            #
            await self.channel_layer.group_send(user_pk, OutgoingEventNewTextMessage(
                random_id=rid,
                text=text,
                sender=self.group_name,
                receiver=user_pk,
                sender_username=self.sender_username
            )._asdict())

        recipient: Optional[AbstractBaseUser] = await get_user_by_pk(user_pk)
        logger.info(f"DB check if user {user_pk} exists resulted in {recipient}")
        if not recipient:
            return ErrorTypes.InvalidUserPk, f"User with pk {user_pk} does not exist"

        logger.info(f"Will save text message from {self.user} to {recipient}")
        msg = await save_text_message(text, from_=self.user, to=recipient)
        await self._after_message_save(msg, rid=rid, user_pk=user_pk)

    async def handle_call_message(self, data: Dict[str, str]):
        pass

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

        print(msg_type)

        if msg_type == MessageTypes.IsTyping:
            return await self.handle_is_typing(data)
        elif msg_type == MessageTypes.TypingStopped:
            return await self.handle_typing_stopped(data)
        elif msg_type == MessageTypes.MessageRead:
            return await self.handle_message_read(data)
        elif msg_type == MessageTypes.FileMessage:
            return await self.handle_file_message(data)
        elif msg_type == MessageTypes.TextMessage:
            return await self.handle_text_message(data)
        elif msg_type == MessageTypes.CallMessage:
            return await self.handle_call_message(data)
        else:
            return ErrorTypes.MessageParsingError, f"Unknown message type {msg_type.name}"

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
