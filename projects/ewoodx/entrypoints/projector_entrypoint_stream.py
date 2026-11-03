"""
eWoodX projector application entrypoint.

Owns runtime configuration and launches the modular
projector composer.

Run from repository root:
    python -m projects.ewoodx.entrypoints.projector_entrypoint_stream
"""

from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from projects.ewoodx.config import (
    CALIBRATION_ROOT,
    PROJECTOR_CALIBRATION_MODE,
)

from projects.ewoodx.operations.projector_composer import (
    EWoodXProjectorComposer,
)


# =============================================================
# PROJECTOR RUNTIME CONFIGURATION
# =============================================================

# Calibration
HOMOGRAPHY_FILE = (
    CALIBRATION_ROOT
    / "projector"
    / PROJECTOR_CALIBRATION_MODE
    / "projector_homography.npz"
)

# Display
FULLSCREEN = True
FRAME_DELAY_MS = 16

# Local sensing measurement
FILE_POLL_INTERVAL = 0.5

# Grasshopper geometry
# 0.0 disables inactivity timeout.
GH_TIMEOUT = 0.0

# Streaming
# When unavailable, local measurement monitoring continues.
ENABLE_STREAMING = True


# =============================================================
# PROJECTOR ENTRYPOINT
# =============================================================

class EWoodXProjectorEntrypoint:
    """
    Configure and launch one eWoodX projector application.

    The entrypoint owns startup configuration.

    The composer owns the running application's lifecycle,
    projection state, streaming, controls, and rendering.
    """

    def __init__(
        self,
        homography_file: str | Path = HOMOGRAPHY_FILE,
        fullscreen: bool = FULLSCREEN,
        frame_delay_ms: int = FRAME_DELAY_MS,
        file_poll_interval: float = FILE_POLL_INTERVAL,
        gh_timeout: float = GH_TIMEOUT,
        enable_streaming: bool = ENABLE_STREAMING,
    ) -> None:

        self.homography_file = Path(homography_file)
        self.fullscreen = bool(fullscreen)
        self.frame_delay_ms = frame_delay_ms
        self.file_poll_interval = file_poll_interval
        self.gh_timeout = gh_timeout
        self.enable_streaming = bool(enable_streaming)

    def run(self) -> None:
        """
        Create and run the configured projector composer.
        """

        composer = EWoodXProjectorComposer(
            homography_file=self.homography_file,
            fullscreen=self.fullscreen,
            frame_delay_ms=self.frame_delay_ms,
            file_poll_interval=self.file_poll_interval,
            gh_timeout=self.gh_timeout,
            enable_streaming=self.enable_streaming,
        )

        composer.run()


def main() -> None:
    entrypoint = EWoodXProjectorEntrypoint()
    entrypoint.run()


if __name__ == "__main__":
    main()