"""
eWoodX controller streaming service.

Sends interactive commands to registered endpoints
and receives their results.
"""

from projects.ewoodx.config import (
    STREAM_HOST,
    CONTROLLER_STREAM_PORT,
    STREAM_CONTROLLER_ID,
    STREAM_CAMERA_ID,
)

from projects.ewoodx.operations.streaming.stream_common import (
    StreamEndpointBase,
    STATUS,
)


class ControllerStreamService(StreamEndpointBase):

    def __init__(
        self,
        agent_id=STREAM_CONTROLLER_ID,
        host=STREAM_HOST,
        port=CONTROLLER_STREAM_PORT,
        on_stream=None,
    ):
        super().__init__(
            agent_id=agent_id,
            roles=["controller"],
            host=host,
            port=port,
            stream_topics=[],
            on_stream=on_stream,
        )

    def start(self, subscribe=None):
        if subscribe is None:
            subscribe = [STATUS]

        super().start(
            subscribe=subscribe,
        )

    def send_sensing_command(
        self,
        command,
        parameters=None,
        target=STREAM_CAMERA_ID,
        request_id=None,
    ):
        return self.send_command(
            target=target,
            command=command,
            parameters=parameters,
            request_id=request_id,
        )

    def get_command_result(self, timeout=None):
        return self.get_result(timeout=timeout)

    def get_latest_status(self):
        return self.get_latest(STATUS)