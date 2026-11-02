"""
eWoodX sensing streaming service.

Publishes live measurements and receives
interactive sensing commands.

The sensing composer owns the service lifecycle.
"""

from projects.ewoodx.config import (
    STREAM_HOST,
    SENSING_STREAM_PORT,
    STREAM_CAMERA_ID,
)

from projects.ewoodx.operations.streaming.stream_common import (
    StreamEndpointBase,
    MEASUREMENT,
)


class SensingStreamService(StreamEndpointBase):

    def __init__(
        self,
        agent_id=STREAM_CAMERA_ID,
        host=STREAM_HOST,
        port=SENSING_STREAM_PORT,
        on_stream=None,
    ):
        super().__init__(
            agent_id=agent_id,
            roles=["sensing"],
            host=host,
            port=port,
            stream_topics=[MEASUREMENT],
            on_stream=on_stream,
        )

    def publish_measurement(
        self,
        measurement,
        frame_id=None,
        valid=True,
    ):
        """
        Publish the latest complete measurement.

        Supports both:
        - Single-timber flat measurement
        - Multi-timber capture-level measurement

        No persistent timber entity is created here.
        """
        self.publish_latest(
            MEASUREMENT,
            measurement,
            frame_id=frame_id,
            valid=bool(valid),
        )

    def get_sensing_command(self, timeout=None):
        return self.get_command(timeout=timeout)

    def report_command_result(
        self,
        command_message,
        success,
        result=None,
    ):
        self.send_command_result(
            target=command_message["source"],
            request_id=command_message["request_id"],
            success=success,
            result=result,
        )