"""
Central eWoodX streaming host.

One host process with dedicated ports for:
- Sensing
- Projector
- Controller

Uses the existing generic StreamHandler.
"""

import copy
import threading

from framework.communication.workflow.stream_handler import (
    StreamHandler,
)

from projects.ewoodx.config import (
    STREAM_BIND_HOST,
    SENSING_STREAM_PORT,
    PROJECTOR_STREAM_PORT,
    CONTROLLER_STREAM_PORT,
)

from projects.ewoodx.operations.streaming.stream_common import (
    MEASUREMENT,
    PROJECTOR,
    STATUS,
    COMMAND,
    COMMAND_RESULT,
    SUBSCRIBE,
    UNSUBSCRIBE,
    STREAM_TOPICS,
    make_message,
)


SENSING = "sensing"
PROJECTOR_CHANNEL = "projector"
CONTROLLER = "controller"


class EWoodXStreamHost:
    """
    Central multi-port stream router.

    Every port has its own StreamHandler.
    Agent IDs must be unique across all ports.
    """

    def __init__(
        self,
        host=STREAM_BIND_HOST,
        sensing_port=SENSING_STREAM_PORT,
        projector_port=PROJECTOR_STREAM_PORT,
        controller_port=CONTROLLER_STREAM_PORT,
    ):
        ports = [
            sensing_port,
            projector_port,
            controller_port,
        ]

        if len(set(ports)) != len(ports):
            raise ValueError(
                "Streaming ports must be unique."
            )

        self._lock = threading.RLock()
        self._running = False

        self._subscriptions = {}

        self._latest = {
            topic: None
            for topic in STREAM_TOPICS
        }

        self._handlers = {}

        port_map = {
            SENSING: sensing_port,
            PROJECTOR_CHANNEL: projector_port,
            CONTROLLER: controller_port,
        }

        for channel, port in port_map.items():
            self._handlers[channel] = StreamHandler(
                host=host,
                port=port,
                on_message=self._make_callback(channel),
            )

    def _make_callback(self, channel):
        def callback(agent, message):
            self._on_message(
                channel,
                agent,
                message,
            )

        return callback

    @property
    def connected_agents(self):
        result = {}

        for channel, handler in self._handlers.items():
            for agent_id in handler.connected_agents:
                result[agent_id] = channel

        return result

    def start(self):
        if self._running:
            raise RuntimeError(
                "Stream host already running."
            )

        started = []

        try:
            for channel, handler in self._handlers.items():
                handler.start()
                started.append(channel)

        except Exception:
            for channel in reversed(started):
                self._handlers[channel].stop()
            raise

        self._running = True

    def stop(self):
        if not self._running:
            return

        self._running = False

        for handler in self._handlers.values():
            handler.stop()

        with self._lock:
            self._subscriptions.clear()

    def _find_agent(self, agent_id):
        """
        Find the channel containing a registered agent.

        Returns None when absent or ambiguous.
        """
        matches = [
            channel
            for channel, handler in self._handlers.items()
            if agent_id in handler.connected_agents
        ]

        if len(matches) != 1:
            return None

        return matches[0]

    def _safe_send(self, agent_id, message):
        channel = self._find_agent(agent_id)

        if channel is None:
            return False

        try:
            self._handlers[channel].send(
                agent_id,
                message,
            )
            return True

        except (ConnectionError, OSError):
            return False

    def _prune_subscriptions(self):
        connected = set(self.connected_agents)

        with self._lock:
            stale = [
                agent_id
                for agent_id in self._subscriptions
                if agent_id not in connected
            ]

            for agent_id in stale:
                self._subscriptions.pop(
                    agent_id,
                    None,
                )

    def _on_message(self, channel, agent, message):
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

        if not all(
            isinstance(topic, str)
            for topic in topics
        ):
            return

        topics = set(topics) & STREAM_TOPICS

        self._prune_subscriptions()

        with self._lock:
            current = self._subscriptions.setdefault(
                agent_id,
                set(),
            )
            current.update(topics)

            cached = [
                copy.deepcopy(self._latest[topic])
                for topic in topics
                if self._latest[topic] is not None
            ]

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
            current.difference_update(
                topic
                for topic in topics
                if isinstance(topic, str)
            )

    def _route_stream(self, sender_id, message):
        message_type = message["type"]

        forwarded = {
            **message,
            "source": sender_id,
        }

        self._prune_subscriptions()

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

        for agent_id in subscribers:
            self._safe_send(
                agent_id,
                forwarded,
            )

    def _route_command(self, sender_id, message):
        target = message.get("target")
        request_id = message.get("request_id")
        command = message.get("command")

        if (
            not isinstance(target, str)
            or not target
            or not isinstance(request_id, str)
            or not request_id
            or not isinstance(command, str)
        ):
            return

        forwarded = {
            **message,
            "source": sender_id,
        }

        delivered = self._safe_send(
            target,
            forwarded,
        )

        if not delivered:
            self._safe_send(
                sender_id,
                make_message(
                    COMMAND_RESULT,
                    target=sender_id,
                    source=target,
                    request_id=request_id,
                    success=False,
                    result={
                        "error": (
                            "Target unavailable or "
                            "command forwarding failed."
                        )
                    },
                ),
            )

    def _route_command_result(self, sender_id, message):
        target = message.get("target")
        request_id = message.get("request_id")

        if (
            not isinstance(target, str)
            or not target
            or not isinstance(request_id, str)
            or not request_id
        ):
            return

        forwarded = {
            **message,
            "source": sender_id,
        }

        self._safe_send(
            target,
            forwarded,
        )