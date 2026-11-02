"""eWoodX distributed communication configuration."""

from projects.ewoodx.config.workspace import (
    EWOODX_REPOSITORY_ROOT,
)


# ---------------------------------------------------------------------
# Agent runtime
# ---------------------------------------------------------------------

AGENTS_RUNTIME_ROOT = (
    EWOODX_REPOSITORY_ROOT
    / "agents_runtime"
)


# ---------------------------------------------------------------------
# Master
# ---------------------------------------------------------------------

MASTER_BIND_HOST = "0.0.0.0"
MASTER_HOST = "127.0.0.1"
MASTER_PORT = 5105
MASTER_FILE_PORT = 5106


# ---------------------------------------------------------------------
# Sensing agent
# ---------------------------------------------------------------------

SENSING_AGENT_ID = "sensing_pc_01"

SENSING_AGENT_ROLES = [
    "sensing",
]

SENSING_AGENT_HOST = "127.0.0.1"
SENSING_AGENT_PORT = 6105

SENSING_AGENT_POLL_INTERVAL = 1.0

# ---------------------------------------------------------------------
# eWoodX streaming
# ---------------------------------------------------------------------

# Central streaming host
STREAM_BIND_HOST = "127.0.0.1"
STREAM_HOST = "127.0.0.1"

# Dedicated ports
SENSING_STREAM_PORT = 6201
PROJECTOR_STREAM_PORT = 6202
CONTROLLER_STREAM_PORT = 6203

# Default endpoint identities
STREAM_CAMERA_ID = "ewoodx_camera_01"
STREAM_PROJECTOR_ID = "ewoodx_projector_01"
STREAM_CONTROLLER_ID = "ewoodx_controller_01"