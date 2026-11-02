"""
eWoodX projector streaming service.

Receives live measurements and projector geometry.

Does not depend on Rhino, Grasshopper, OpenCV,
or the existing projector viewer implementation.
"""

from projects.ewoodx.config import (
    STREAM_HOST,
    PROJECTOR_STREAM_PORT,
    STREAM_PROJECTOR_ID,
)

from projects.ewoodx.operations.streaming.stream_common import (
    StreamEndpointBase,
    MEASUREMENT,
    PROJECTOR,
)


class ProjectorStreamService(StreamEndpointBase):

    def __init__(
        self,
        agent_id=STREAM_PROJECTOR_ID,
        host=STREAM_HOST,
        port=PROJECTOR_STREAM_PORT,
        on_stream=None,
    ):
        super().__init__(
            agent_id=agent_id,
            roles=["projector"],
            host=host,
            port=port,
            stream_topics=[PROJECTOR],
            on_stream=on_stream,
        )

    def start(self, subscribe=None):
        if subscribe is None:
            subscribe = [
                MEASUREMENT,
                PROJECTOR,
            ]

        super().start(
            subscribe=subscribe,
        )

    def publish_geometry(self, geometry):
        """
        Publish latest projector-specific geometry.

        Geometry structure remains application-defined.
        """
        self.publish_latest(
            PROJECTOR,
            geometry,
        )

    def get_latest_measurement(self):
        return self.get_latest(MEASUREMENT)

    def get_latest_geometry(self):
        return self.get_latest(PROJECTOR)