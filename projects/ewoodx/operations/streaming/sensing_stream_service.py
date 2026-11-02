"""
eWoodX project-specific streaming service.

Uses the existing generic framework:
    Agent
    StreamHandler
    StreamClient

Features:
- Persistent bidirectional JSON streaming
- Local or remote host configuration
- Camera measurement publication
- Projector / viewer subscriptions
- Latest-value measurement buffers
- FIFO interactive command queue
- Request / response correlation
- Latest measurement replay on subscription
- No camera, projector, database, or file I/O

This module does not modify the event-based workflow.
"""

import copy
import json
import queue
import threading
import time
import uuid

from typing import Any, Callable

from framework.communication.core import Agent
from framework.communication.workflow.stream_handler import (
    StreamHandler,
)
from framework.communication.workflow.stream_client import (
    StreamClient,
)


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 5107

MEASUREMENT = "ewoodx.measurement"
PROJECTOR = "ewoodx.projector"
STATUS = "ewoodx.status"
COMMAND = "ewoodx.command"
COMMAND_RESULT = "ewoodx.command_result"
SUBSCRIBE = "ewoodx.subscribe"
UNSUBSCRIBE = "ewoodx.unsubscribe"

STREAM_TOPICS = {
    MEASUREMENT,
    PROJECTOR,
    STATUS,
}

CONTROL_COMMANDS = {
    "save",
    "set_thickness",
    "stop",
    "pause",
    "resume",
    "get_status",
}


def _json_copy(value):
    """
    Validate that a value can travel over the
    generic JSON stream and return a detached copy.
    """
    return json.loads(
        json.dumps(value, allow_nan=False)
    )


def _message(message_type, **fields):
    return {
        "type": message_type,
        "timestamp": time.time(),
        **fields,
    }


class LatestValue:
    """
    Thread-safe single-value buffer.

    Each new measurement replaces the previous one.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._value = None
        self._revision = 0

    def update(self, value):
        with self._lock:
            self._value = value
            self._revision += 1
            return self._revision

    def get(self):
        with self._lock:
            return (
                self._revision,
                copy.deepcopy(self._value),
            )


class EWoodXStreamHost:
    """
    Central stream router.

    Runs locally for the first development stage.
    Can later run on the master PC.

    Registered clients subscribe to topics.
    Commands are routed to a target endpoint.
    """

    def __init__(
        self,
        host=DEFAULT_HOST,
        port=DEFAULT_PORT,
    ):
        self.host = host
        self.port = port

        self._lock = threading.RLock()
        self._subscriptions = {}
        self._latest = {
            topic: None
            for topic in STREAM_TOPICS
        }

        self._handler = StreamHandler(
            host=host,
            port=port,
            on_message=self._on_message,
        )

        self._running = False

    @property
    def connected_agents(self):
        return self._handler.connected_agents

    def start(self):
        if self._running:
            raise RuntimeError(
                "Stream host is already running."
            )

        self._handler.start()
        self._running = True

    def stop(self):
        if not self._running:
            return

        self._running = False
        self._handler.stop()

        with self._lock:
            self._subscriptions.clear()

    def _safe_send(self, agent_id, message):
        try:
            self._handler.send(
                agent_id,
                message,
            )
            return True

        except (ConnectionError, OSError):
            return False

    def _on_message(self, agent, message):
        """
        Called by the generic StreamHandler.

        This callback must not perform camera,
        projector, or database operations.
        """
        message_type = message.get("type")
        sender_id = agent.agent_id

        if message_type == SUBSCRIBE:
            self._subscribe(sender_id, message)
            return

        if message_type == UNSUBSCRIBE:
            self._unsubscribe(sender_id, message)
            return

        if message_type in STREAM_TOPICS:
            self._route_stream(
                sender_id,
                message,
            )
            return

        if message_type == COMMAND:
            self._route_command(
                sender_id,
                message,
            )
            return

        if message_type == COMMAND_RESULT:
            self._route_command_result(
                sender_id,
                message,
            )
            return

    def _subscribe(self, agent_id, message):
        topics = message.get("topics", [])

        if not isinstance(topics, list):
            return

        topics = set(topics) & STREAM_TOPICS

        with self._lock:
            current = self._subscriptions.setdefault(
                agent_id,
                set(),
            )
            current.update(topics)

            cached = [
                copy.deepcopy(self._latest[t])
                for t in topics
                if self._latest[t] is not None
            ]

        # Replay the latest known value.
        for item in cached:
            self._safe_send(agent_id, item)

    def _unsubscribe(self, agent_id, message):
        topics = message.get("topics", [])

        if not isinstance(topics, list):
            return

        with self._lock:
            current = self._subscriptions.get(
                agent_id,
                set(),
            )
            current.difference_update(topics)

    def _route_stream(self, sender_id, message):
        message_type = message["type"]

        forwarded = {
            **message,
            "source": sender_id,
        }

        with self._lock:
            self._latest[message_type] = (
                copy.deepcopy(forwarded)
            )

            subscribers = [
                agent_id
                for agent_id, topics
                in self._subscriptions.items()
                if message_type in topics
                and agent_id != sender_id
            ]

        connected = set(
            self._handler.connected_agents
        )

        for agent_id in subscribers:
            if agent_id in connected:
                self._safe_send(
                    agent_id,
                    forwarded,
                )

    def _route_command(self, sender_id, message):
        target = message.get("target")
        request_id = message.get("request_id")

        if not isinstance(target, str) or not target:
            return

        if not isinstance(request_id, str) or not request_id:
            return

        if target not in self._handler.connected_agents:
            self._safe_send(
                sender_id,
                _message(
                    COMMAND_RESULT,
                    request_id=request_id,
                    target=sender_id,
                    source=target,
                    success=False,
                    result={
                        "error": "Target is not connected."
                    },
                ),
            )
            return

        forwarded = {
            **message,
            "source": sender_id,
        }

        self._safe_send(target, forwarded)

    def _route_command_result(self, sender_id, message):
        target = message.get("target")

        if not isinstance(target, str) or not target:
            return

        forwarded = {
            **message,
            "source": sender_id,
        }

        self._safe_send(target, forwarded)


class EWoodXStreamEndpoint:
    """
    Registered streaming endpoint.

    Possible roles:
        sensing
        projector
        controller

    Measurement publication is asynchronous:
    only the latest unsent update is retained.

    Commands are received into a FIFO queue.
    """

    def __init__(
        self,
        agent_id,
        roles,
        host=DEFAULT_HOST,
        port=DEFAULT_PORT,
        on_measurement: Callable | None = None,
        on_projector: Callable | None = None,
        on_status: Callable | None = None,
        command_queue_size=128,
    ):
        self.agent_id = agent_id
        self.roles = list(roles)

        self.agent = Agent(
            agent_id=agent_id,
            roles=self.roles,
        )

        self._callbacks = {
            MEASUREMENT: on_measurement,
            PROJECTOR: on_projector,
            STATUS: on_status,
        }

        self.latest_measurement = LatestValue()
        self.latest_projector = LatestValue()
        self.latest_status = LatestValue()

        self.commands = queue.Queue(
            maxsize=command_queue_size
        )

        self.results = queue.Queue()

        self._outgoing = LatestValue()
        self._wake = threading.Event()
        self._stop = threading.Event()
        self._sender_thread = None

        self._send_lock = threading.Lock()

        self._client = StreamClient(
            agent=self.agent,
            host=host,
            port=port,
            on_message=self._on_message,
            on_disconnect=self._on_disconnect,
        )

    @property
    def connected(self):
        return self._client.registered

    def start(self, topics=None):
        """
        Connect, register, subscribe and start
        the asynchronous measurement sender.
        """
        self._client.connect()

        try:
            if topics:
                self._client.send(
                    _message(
                        SUBSCRIBE,
                        topics=list(topics),
                    )
                )

            self._stop.clear()
            self._wake.clear()

            self._sender_thread = threading.Thread(
                target=self._sender_loop,
                name=f"{self.agent_id}-stream-sender",
                daemon=True,
            )
            self._sender_thread.start()

        except Exception:
            self._client.close()
            raise

    def stop(self):
        self._stop.set()
        self._wake.set()

        thread = self._sender_thread

        if (
            thread is not None
            and thread is not threading.current_thread()
        ):
            thread.join(timeout=2.0)

        self._sender_thread = None
        self._client.close()

    def _send(self, message):
        with self._send_lock:
            self._client.send(message)

    def publish_measurement(
        self,
        measurement,
        frame_id=None,
        valid=True,
    ):
        """
        Queue the latest measurement without
        waiting for network transmission.
        """
        payload = _json_copy(measurement)

        message = _message(
            MEASUREMENT,
            frame_id=frame_id,
            valid=bool(valid),
            payload=payload,
        )

        self._outgoing.update(message)
        self._wake.set()

    def publish_projector(self, geometry):
        """
        Publish projector-specific geometry.

        Currently sends immediately. Use this
        for relatively low-frequency updates.
        """
        self._send(
            _message(
                PROJECTOR,
                payload=_json_copy(geometry),
            )
        )

    def publish_status(self, status):
        self._send(
            _message(
                STATUS,
                payload=_json_copy(status),
            )
        )

    def send_command(
        self,
        target,
        command,
        parameters=None,
        request_id=None,
    ):
        if command not in CONTROL_COMMANDS:
            raise ValueError(
                f"Unsupported command: {command}"
            )

        request_id = request_id or str(
            uuid.uuid4()
        )

        self._send(
            _message(
                COMMAND,
                target=target,
                request_id=request_id,
                command=command,
                parameters=_json_copy(
                    parameters or {}
                ),
            )
        )

        return request_id

    def send_command_result(
        self,
        target,
        request_id,
        success,
        result=None,
    ):
        self._send(
            _message(
                COMMAND_RESULT,
                target=target,
                request_id=request_id,
                success=bool(success),
                result=_json_copy(
                    result or {}
                ),
            )
        )

    def get_command(self, timeout=None):
        """
        Called by the composer, not by the
        network receiver thread.
        """
        try:
            return self.commands.get(
                timeout=timeout
                if timeout is not None
                else 0,
            )
        except queue.Empty:
            return None

    def get_result(self, timeout=None):
        try:
            return self.results.get(
                timeout=timeout
                if timeout is not None
                else 0,
            )
        except queue.Empty:
            return None

    def _sender_loop(self):
        last_revision = 0

        while not self._stop.is_set():
            self._wake.wait(timeout=0.2)
            self._wake.clear()

            if self._stop.is_set():
                break

            revision, message = (
                self._outgoing.get()
            )

            if (
                message is None
                or revision == last_revision
            ):
                continue

            try:
                self._send(message)
                last_revision = revision

            except (ConnectionError, OSError):
                # No unbounded backlog is created.
                # The newest measurement remains
                # available for later inspection.
                break

    def _on_message(self, message):
        message_type = message.get("type")

        if message_type == MEASUREMENT:
            self.latest_measurement.update(
                message
            )

        elif message_type == PROJECTOR:
            self.latest_projector.update(
                message
            )

        elif message_type == STATUS:
            self.latest_status.update(
                message
            )

        elif message_type == COMMAND:
            if message.get("target") != self.agent_id:
                return

            try:
                self.commands.put_nowait(
                    message
                )
            except queue.Full:
                # Explicit failure; do not silently
                # discard a control command.
                self.send_command_result(
                    target=message.get("source"),
                    request_id=message.get("request_id"),
                    success=False,
                    result={
                        "error": "Command queue is full."
                    },
                )
            return

        elif message_type == COMMAND_RESULT:
            if message.get("target") == self.agent_id:
                self.results.put(message)
            return

        callback = self._callbacks.get(
            message_type
        )

        if callback is not None:
            try:
                callback(message)
            except Exception as error:
                print(
                    "[eWoodX stream] Callback error:",
                    error,
                )

    def _on_disconnect(self):
        self._wake.set()