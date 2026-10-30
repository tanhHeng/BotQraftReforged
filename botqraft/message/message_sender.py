"""Synchronous validation/snapshot boundary for typed QQ operations."""
from concurrent.futures import Future
from typing import TYPE_CHECKING, Any, Awaitable, Callable
from typing_extensions import Self

if TYPE_CHECKING:
    from botqraft.runtime import Runtime
    from botqraft.command.command_source import QQCommandSource
import asyncio
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import heapq
import math
from threading import RLock, Timer
import time

from botqraft.event.qq_event import QQEvent
from botqraft.event.qq_interaction import QQInteraction
from botqraft.message.message_received import QQMessageReceived
from botqraft.message.message_receipt import QQMessageReceipt
from botqraft.message.user import C2C, Group
from botqraft.message.media import QMediaBase
from botqraft.message.qtext.text import QTextBase, QText
from botqraft.network.exception import NetworkError, NotReadyError, ResultUnknownError
from botqraft.utils.exception import PassiveReplyExpiredError


@dataclass
class _Passive:
    first_seen: float
    expires_at: float
    sequence: int = 0


class MessageSender:
    """Validated QQ sends, deletes and interaction responses with payload snapshots."""
    # Platform passive-reply windows: group 5 minutes, C2C 60 minutes (https://bot.q.qq.com/wiki/develop/api-v2/server-inter/message/overview.html).
    PASSIVE_LIFETIME = {'group': 300, 'c2c': 3600}

    def __init__(self: Self, runtime: "Runtime") -> None:
        """Create the synchronous QQ operation validation and payload snapshot boundary.
        
        :param runtime: Runtime providing translation, network submission and the QQ API client.
        :return: The method returns no value.
        """
        self.runtime = runtime
        self._lock = RLock()
        self._passive = {}
        self._expirations = []
        self._interactions = set()
        self._expiry_timer = None
        self._timer_generation = 0
        self._closed = False
        self._time_observation = None
        self._time_warning_generation = 0


    def get_time_observation(self):
        """Return the latest valid receive-time clock observation."""
        with self._lock:
            return self._time_observation

    def _arm_expiry(self: Self) -> None:
        if not self._closed and self._expiry_timer is None and self._expirations:
            delay = max(0, self._expirations[0][0] - time.monotonic())
            self._timer_generation += 1
            self._expiry_timer = Timer(delay, self._expire_passive, args=(self._timer_generation,))
            self._expiry_timer.daemon = True
            self._expiry_timer.start()

    def _expire_passive(self: Self, generation: int) -> None:
        with self._lock:
            if generation != self._timer_generation:
                return
            self._expiry_timer = None
            self._cleanup(time.monotonic())
            self._arm_expiry()

    def close(self: Self) -> None:
        """Stop passive expiry scheduling and discard retained passive contexts.
        
        :return: The method returns no value.
        """
        with self._lock:
            self._closed = True
            self._timer_generation += 1
            if self._expiry_timer is not None:
                self._expiry_timer.cancel()
                self._expiry_timer = None
            self._passive.clear()
            self._expirations.clear()

    @staticmethod
    def _string(value: str | None, name: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f'{name} must be a non-empty string')
        return value

    @staticmethod
    def _route(target: Group | C2C) -> tuple[str, str]:
        if not isinstance(target, (Group, C2C)):
            raise TypeError('target must be Group or C2C')
        scene, conversation = target.route()
        scene = getattr(scene, 'value', scene)
        if scene not in ('group', 'c2c'):
            raise ValueError('Only group and c2c are supported')
        return scene, MessageSender._string(conversation, 'conversation')

    @staticmethod
    def _incoming_route(event: QQEvent) -> tuple[str, str]:
        payload = event.raw_payload
        data = payload.get('d')
        if not isinstance(data, dict):
            raise ValueError('event has no object data')
        if payload.get('t') in ('GROUP_MESSAGE_CREATE', 'GROUP_AT_MESSAGE_CREATE', 'GROUP_ADD_ROBOT', 'GROUP_MSG_RECEIVE'):
            return 'group', MessageSender._string(data.get('group_openid'), 'group_openid')
        if payload.get('t') == 'C2C_MESSAGE_CREATE':
            author = data.get('author')
            if not isinstance(author, dict):
                raise ValueError('message has no author')
            return 'c2c', MessageSender._string(author.get('user_openid'), 'user_openid')
        raise ValueError('event does not have a supported message route')

    def _ready(self: Self) -> None:
        if self.runtime.is_stopping() or not self.runtime.is_ready() or not self.runtime.gateway.is_ready():
            raise NotReadyError('QQ runtime/gateway is not ready for new operations')

    def _cleanup(self: Self, now: float) -> None:
        while self._expirations and self._expirations[0][0] <= now:
            expiry, key = heapq.heappop(self._expirations)
            entry = self._passive.get(key)
            if entry is not None and entry.expires_at == expiry:
                del self._passive[key]

    @staticmethod
    def _platform_time(event: QQEvent) -> float:
        timestamp = event.raw_payload.get('d', {}).get('timestamp')
        relationship = event.raw_payload.get('t') in ('GROUP_ADD_ROBOT', 'GROUP_MSG_RECEIVE')
        try:
            if relationship:
                if isinstance(timestamp, bool) or not isinstance(timestamp, int):
                    raise ValueError
                value = float(timestamp)
            else:
                if not isinstance(timestamp, str):
                    raise ValueError
                parsed = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                if parsed.tzinfo is None or parsed.utcoffset() is None:
                    raise ValueError
                value = parsed.timestamp()
            if not math.isfinite(value) or value <= 0:
                raise ValueError
            return value
        except (ValueError, TypeError, OverflowError, OSError):
            raise ValueError('passive context lacks a trustworthy original platform timestamp') from None

    def register_incoming(self: Self, event: QQEvent) -> None:
        """Record original supported incoming contexts and their platform-derived passive deadlines.
        
        :param event: Original QQ event; unsupported, malformed or already expired contexts are not retained.
        :return: The method returns no value.
        """
        if not isinstance(event, QQEvent):
            raise TypeError('incoming must be QQEvent')
        if self._closed:
            return
        kind = event.raw_payload.get('t')
        if kind not in ('GROUP_MESSAGE_CREATE', 'GROUP_AT_MESSAGE_CREATE', 'C2C_MESSAGE_CREATE',
                        'GROUP_ADD_ROBOT', 'GROUP_MSG_RECEIVE'):
            return
        try:
            scene, conversation = self._incoming_route(event)
            association = event.raw_payload.get('id') if kind in ('GROUP_ADD_ROBOT', 'GROUP_MSG_RECEIVE') else event.raw_payload['d'].get('id')
            association = self._string(association, 'passive association id')
        except (ValueError, KeyError):
            return  # Parsing/command-source validation reports malformed incoming facts.
        field = 'event_id' if kind in ('GROUP_ADD_ROBOT', 'GROUP_MSG_RECEIVE') else 'msg_id'
        key = (scene, conversation, field, association)
        now = time.monotonic()
        try:
            platform_time = self._platform_time(event)
        except ValueError:
            event._passive_deadline = float('-inf')
            return
        received_wall = time.time()
        offset = platform_time - received_wall
        status = 'error' if offset > 15 else 'warning' if offset > 5 else 'normal'
        with self._lock:
            self._time_observation = (offset, received_wall, status)
            generation = self.runtime.api_client.token_provider.refresh_generation
            warn = status == 'warning' and generation > self._time_warning_generation
            if warn:
                self._time_warning_generation = generation
        if warn:
            self.runtime.logger.warning('Platform time ahead by %.1fs; check system clock.', offset)
        event._timestamp_offset = offset
        if status == 'error':
            event._passive_deadline = float('-inf')
            return
        lifetime = self.PASSIVE_LIFETIME[scene]
        deadline = min(getattr(event, 'received_at', now) + lifetime,
                       now + lifetime - max(0, -offset))
        with self._lock:
            self._cleanup(now)
            if deadline <= now:
                event._passive_deadline = deadline
                return
            if key not in self._passive:
                first = getattr(event, 'received_at', now)
                entry = _Passive(first, deadline)
                self._passive[key] = entry
                heapq.heappush(self._expirations, (entry.expires_at, key))
                self._arm_expiry()
            entry = self._passive[key]
            event._passive_deadline = entry.expires_at

    def _passive_seq(self: Self, scene: str, conversation: str, field: str, association: str, context: QQEvent | None) -> int:
        if not isinstance(context, QQEvent):
            raise ValueError('passive sending requires the original incoming event')
        expected_route = self._incoming_route(context)
        if expected_route != (scene, conversation):
            raise ValueError('passive context belongs to a different conversation')
        expected = context.raw_payload.get('id') if field == 'event_id' else context.raw_payload['d'].get('id')
        if expected != association:
            raise ValueError('passive id does not match the original incoming event')
        if getattr(context, '_timestamp_offset', 0) > 15:
            raise ValueError('platform timestamp is more than 15 seconds ahead of local receive time')
        key = (scene, conversation, field, association)
        now = time.monotonic()
        with self._lock:
            self._cleanup(now)
            entry = self._passive.get(key)
            if entry is None or now >= entry.expires_at or now >= getattr(context, '_passive_deadline', float('-inf')):
                raise PassiveReplyExpiredError('passive association is expired or was not registered on receipt')
            entry.sequence += 1
            return entry.sequence

    def _reference(self: Self, message: QQMessageReceived | QQMessageReceipt | None, scene: str, conversation: str) -> dict[str, str] | None:
        if message is None:
            return None
        if isinstance(message, QQMessageReceived):
            route = self._incoming_route(message)
            data = message.raw_payload.get('d', {})
            ext = data.get('message_scene', {}).get('ext') if isinstance(data.get('message_scene'), dict) else None
            index = None
            if isinstance(ext, list):
                for item in ext:
                    if isinstance(item, str) and item.startswith('msg_idx='):
                        index = item.partition('=')[2]
                        break
        elif isinstance(message, QQMessageReceipt):
            route = (getattr(message.scene, 'value', message.scene), message.conversation)
            ext = message.raw_response.get('ext_info')
            index = ext.get('ref_idx') if isinstance(ext, dict) else None
        else:
            raise TypeError('refer_msg must be QQMessageReceived, QQMessageReceipt or None')
        if route != (scene, conversation):
            raise ValueError('reference belongs to a different conversation')
        return {'message_id': self._string(index, 'reference index')}

    def _content(self: Self, message: str | QTextBase) -> dict[str, Any]:
        if not isinstance(message, (str, QTextBase)):
            raise TypeError('message must be str, QTextBase or QMediaBase')
        evaluated = self.runtime.translation_manager.evaluate(message)
        text = QText(evaluated) if isinstance(evaluated, str) else evaluated
        if not isinstance(text, QTextBase):
            raise TypeError('evaluated message must be str or QTextBase')
        payload = deepcopy(text.to_payload())
        if not isinstance(payload, dict):
            raise TypeError('message encoder must return a dict')
        # QQ does not render mention tags in plain-text messages yet; keep sending them until the platform adapts.
        if payload.get('msg_type') == 0 and '<qqbot-at-user ' in payload.get('content', ''):
            self.runtime.logger.warning('QQ does not render QTextAt mentions in plain-text messages yet; combine them into QMarkdown to show @')
        return payload

    def send(self: Self, target: Group | C2C, message: str | QTextBase | QMediaBase, *, refer_msg: QQMessageReceived | QQMessageReceipt | None = None, msg_id: str | None = None, event_id: str | None = None, passive_context: QQEvent | None = None) -> Future[QQMessageReceipt]:
        """Validate routing and content synchronously, snapshot the payload, then submit the send operation.
        
        :param target: Group or C2C conversation target.
        :param message: Literal or typed QQ text, or media uploaded to the target conversation before sending. Existing delayed translation objects are evaluated before payload snapshotting.
        :param refer_msg: Optional received message or receipt reference from the same conversation.
        :param msg_id: Optional original message ID for a passive reply; mutually exclusive with event_id.
        :param event_id: Optional original GROUP_ADD_ROBOT or GROUP_MSG_RECEIVE event ID for a passive reply.
        :param passive_context: Original registered incoming event required when a passive association ID is supplied.
        :return: A future yielding the successful receipt or the network operation exception.
        """
        scene, conversation = self._route(target)
        if msg_id is not None and event_id is not None:
            raise ValueError('msg_id and event_id are mutually exclusive')
        if msg_id is not None:
            self._string(msg_id, 'msg_id')
        if event_id is not None:
            self._string(event_id, 'event_id')
            if not isinstance(passive_context, QQEvent) or passive_context.raw_payload.get('t') not in ('GROUP_ADD_ROBOT', 'GROUP_MSG_RECEIVE'):
                raise ValueError('event passive sending only supports GROUP_ADD_ROBOT/GROUP_MSG_RECEIVE')
        if passive_context is not None and msg_id is None and event_id is None:
            raise ValueError('passive context requires msg_id or event_id')
        media = message if isinstance(message, QMediaBase) else None
        payload = {} if media is not None else self._content(message)
        reference = self._reference(refer_msg, scene, conversation)
        if reference is not None:
            payload['message_reference'] = reference
        self._ready()
        deadline = None
        if msg_id is not None or event_id is not None:
            field, association = ('msg_id', msg_id) if msg_id is not None else ('event_id', event_id)
            sequence = self._passive_seq(scene, conversation, field, association, passive_context)
            deadline = passive_context._passive_deadline
            payload[field] = association
            if msg_id is not None:
                payload['msg_seq'] = sequence

        async def send_snapshot() -> QQMessageReceipt:
            if media is not None:
                payload['msg_type'] = 7
                payload['media'] = {'file_info': await self._upload_media(scene, conversation, media)}
                if deadline is not None and time.monotonic() >= deadline:
                    raise PassiveReplyExpiredError('passive reply window ended during media upload')
            raw = await self.runtime.api_client.send_message(scene, conversation, payload)
            return QQMessageReceipt(raw, scene, conversation)

        return self.runtime.network_loop.submit(send_snapshot(), operation=f'send {scene} message')

    async def _upload_media(self: Self, scene: str, conversation: str, media: QMediaBase) -> str:
        api = self.runtime.api_client
        if media.url is not None:
            return (await api.upload_media_url(scene, conversation, media.file_type, media.url, media.name))['file_info']
        reader = media._open()
        try:
            digest = await asyncio.to_thread(reader.digest)
            plan = await api.upload_prepare(scene, conversation, media.file_type, media.name, digest)
            parts = sorted(plan.get('parts', []), key=lambda part: part['index'])
            config = plan.get('upload_config', {})
            retry_timeout = config.get('retry_timeout', 300)
            retry_delay = config.get('retry_delay', 1)
            size = digest['size']
            block_size = int(plan['block_size']) if parts else 0
            for position, part in enumerate(parts):
                # Byte offsets follow plan order; part['index'] is only echoed back to the platform.
                offset = position * block_size
                chunk, chunk_md5 = await asyncio.to_thread(reader.read_part, offset, min(block_size, size - offset))
                url = part['presigned_url']
                await self._retry_upload_step(lambda timeout: api.upload_part(url, chunk, timeout), retry_timeout, retry_delay)
                await self._retry_upload_step(
                    lambda timeout: api.upload_part_finish(scene, conversation, plan['upload_id'], part['index'], len(chunk), chunk_md5, timeout),
                    retry_timeout, retry_delay)
            return (await api.upload_media_merge(scene, conversation, media.file_type, plan['upload_id'], media.name))['file_info']
        finally:
            await asyncio.to_thread(reader.close)

    async def _retry_upload_step(self: Self, step: Callable[[float], Awaitable[None]], retry_timeout: int, retry_delay: int) -> None:
        # Only per-chunk steps are retried: repeating them cannot produce a duplicate message.
        # Cancellation propagates from these steps, so it is never mistaken for a retryable failure.
        if retry_timeout <= 0:
            return await step(self.runtime.get_config().http.timeout)
        deadline = time.monotonic() + retry_timeout
        while True:
            try:
                return await step(deadline - time.monotonic())
            except NetworkError as error:
                retry = isinstance(error, ResultUnknownError) or error.retryable or error.err_code == 40093001
                # A 1 s floor prevents a tight request loop and leaves every retry a usable time budget.
                delay = max(retry_delay, 1, error.retry_after or 0)
                if not retry or time.monotonic() + delay >= deadline:
                    raise
                await asyncio.sleep(delay)

    def reply(self: Self, source: "QQCommandSource", message: str | QTextBase | QMediaBase, *, refer_msg: QQMessageReceived | QQMessageReceipt | bool | None = None) -> Future[QQMessageReceipt]:
        """Submit a passive reply using the command source original message and target.
        
        :param source: QQ command source with an original incoming message and non-empty message ID.
        :param message: Literal or typed QQ text, or media uploaded before the passive reply is sent.
        :param refer_msg: True quotes the original message; False or None omits quoting, otherwise a same-conversation message or receipt.
        :return: A future yielding the successful receipt or the operation exception.
        """
        from botqraft.command.command_source import QQCommandSource
        if not isinstance(source, QQCommandSource):
            raise TypeError('reply requires QQCommandSource')
        msg_id = self._string(source.msg_id, 'source msg_id')
        origin = source.message_received
        if not isinstance(origin, QQMessageReceived):
            raise ValueError('source has no original incoming message')
        if refer_msg is True:
            refer_msg = origin
        elif refer_msg is False:
            refer_msg = None
        scene, conversation = self._incoming_route(origin)
        target = Group(conversation) if scene == 'group' else C2C(conversation)
        return self.send(target, message, refer_msg=refer_msg, msg_id=msg_id, passive_context=origin)

    def reply_event(self: Self, event: QQEvent, message: str | QTextBase | QMediaBase, *, refer_msg: QQMessageReceived | QQMessageReceipt | None = None) -> Future[QQMessageReceipt]:
        """Submit a passive group reply associated with an original supported relationship event.
        
        :param event: Original GROUP_ADD_ROBOT or GROUP_MSG_RECEIVE event with a valid event ID.
        :param message: Literal or typed QQ text, or media uploaded before the passive reply is sent.
        :param refer_msg: Optional received message or receipt reference from the same conversation.
        :return: A future yielding the successful receipt or the operation exception.
        """
        if not isinstance(event, QQEvent) or event.raw_payload.get('t') not in ('GROUP_ADD_ROBOT', 'GROUP_MSG_RECEIVE'):
            raise TypeError('reply_event requires GROUP_ADD_ROBOT or GROUP_MSG_RECEIVE QQEvent')
        scene, conversation = self._incoming_route(event)
        event_id = self._string(event.raw_payload.get('id'), 'event_id')
        return self.send(Group(group_openid=conversation), message, refer_msg=refer_msg,
                         event_id=event_id, passive_context=event)

    def delete_message(self: Self, message: QQMessageReceived | QQMessageReceipt) -> Future[None]:
        """Validate message routing facts and submit deletion of a received or sent message.
        
        :param message: Original received message or send receipt containing the message ID and route.
        :return: A future completed with None on successful deletion or with the operation exception.
        """
        if isinstance(message, QQMessageReceived):
            scene, conversation = self._incoming_route(message)
            id = self._string(message.raw_payload['d'].get('id'), 'message id')
        elif isinstance(message, QQMessageReceipt):
            scene, conversation = getattr(message.scene, 'value', message.scene), message.conversation
            id = self._string(message.raw_response.get('id'), 'message id')
        else:
            raise TypeError('delete_message requires QQMessageReceived or QQMessageReceipt')
        self._string(conversation, 'conversation')
        if scene not in ('group', 'c2c'):
            raise ValueError('Only group and c2c are supported')
        self._ready()
        return self.runtime.network_loop.submit(self.runtime.api_client.delete_message(scene, conversation, id),
                                                operation=f'delete {scene} message')

    def delete_message_with_id(self: Self, target: Group | C2C, id: str) -> Future[None]:
        """Validate a target and explicit message ID, then submit deletion.
        
        :param target: Group or C2C conversation containing the message.
        :param id: Non-empty official message ID to delete.
        :return: A future completed with None on successful deletion or with the operation exception.
        """
        scene, conversation = self._route(target)
        id = self._string(id, 'message id')
        self._ready()
        return self.runtime.network_loop.submit(self.runtime.api_client.delete_message(scene, conversation, id),
                                                operation=f'delete {scene} message')

    def respond_interaction(self: Self, event: QQInteraction, code: Enum | int) -> Future[None]:
        """Validate and submit one response for an interaction ID.
        
        :param event: Received QQ interaction with a valid original interaction ID.
        :param code: An integer from 0 through 5 or an enum with such an integer value; booleans are rejected.
        :return: A future completed with None on success. Definitely unsent failures release the ID; an unknown network result retains it.
        """
        if not isinstance(event, QQInteraction):
            raise TypeError('respond_interaction requires QQInteraction')
        value = code.value if isinstance(code, Enum) else code
        if isinstance(value, bool) or not isinstance(value, int) or value not in range(6):
            raise ValueError('interaction response code must be an integer from 0 through 5')
        data = event.raw_payload.get('d')
        id = self._string(data.get('id') if isinstance(data, dict) else None, 'interaction id')
        self._ready()
        with self._lock:
            if id in self._interactions:
                raise ValueError('this interaction response is already submitted')
            self._interactions.add(id)

        async def respond_snapshot() -> None:
            try:
                await self.runtime.api_client.respond_interaction(id, value)
            except asyncio.CancelledError:
                # ApiClient converts cancellation after transmission to UNKNOWN;
                # plain cancellation here is therefore definitely pre-transmission.
                with self._lock:
                    self._interactions.discard(id)
                raise
            except NetworkError as error:
                if not isinstance(error, ResultUnknownError):
                    with self._lock:
                        self._interactions.discard(id)
                raise

        try:
            return self.runtime.network_loop.submit(respond_snapshot(), operation='respond interaction')
        except BaseException:
            with self._lock:
                self._interactions.discard(id)
            raise
