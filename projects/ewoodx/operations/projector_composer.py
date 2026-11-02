"""
eWoodX - Projector Composer

Main application for the modular eWoodX projection system.

Coordinates:
- ProjectorState
- ProjectorGeometry
- ProjectorRenderer
- ProjectorControls
- ProjectorStreamService

Data sources:
- Local timber measurement JSON
- Live sensing measurement stream
- Complete Grasshopper geometry stream

Operation:
- Loads the latest local timber measurement at startup.
- Automatically attempts to connect to the streaming host.
- Falls back to local JSON monitoring if streaming is unavailable.
- Uses live sensing measurements when received.
- Displays Grasshopper geometry with priority while active.
- Retains the latest sensing measurement independently.
- Restores sensing projection when Grasshopper becomes inactive.

Configuration:
- Runtime settings are defined at the beginning of this file.
- Streaming is enabled automatically.
- Grasshopper inactivity timeout is optional.
- No command-line arguments are required.

Execution:
- Run directly from VS Code.
- Or execute as a module from the repository root:

    python -m projects.ewoodx.operations.projector_composer

The legacy projector_live_viewer.py remains independent.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import cv2


# -------------------------------------------------------------
# Project root resolution
# -------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[3]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from projects.ewoodx.config import (
    CALIBRATION_ROOT,
    PROJECTOR_RUNTIME_ROOT,
    PROJECTOR_CALIBRATION_MODE,
    PROJECTOR_HEIGHT_MM,
    PROJECTOR_POS_X_MM,
    PROJECTOR_POS_Y_MM,
    PROJECTOR_OFFSET_X_MM,
    PROJECTOR_OFFSET_Y_MM,
    TIMBER_THICKNESS_MM,
)

from projects.ewoodx.operations.projection.projector_state import (
    ProjectorState,
)

from projects.ewoodx.operations.projection.projector_geometry import (
    ProjectorGeometry,
)

from projects.ewoodx.operations.projection.projector_renderer import (
    ProjectorRenderer,
)

from projects.ewoodx.operations.projection.projector_controls import (
    ProjectorControls,
)

from projects.ewoodx.operations.streaming.projector_stream_service import (
    ProjectorStreamService,
)

# =============================================================
# PROJECTOR CONFIGURATION
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
# 0.0 = timeout disabled
GH_TIMEOUT = 0.0

# Streaming is always enabled.
# If unavailable at startup, local JSON monitoring continues.


class EWoodXProjectorComposer:
    """
    Application coordinator for the modular projector.

    Responsibilities:
    - Initialize projection modules.
    - Start and stop streaming.
    - Route sensing and Grasshopper stream updates.
    - Execute requested lifecycle actions.
    - Coordinate rendering and keyboard input.
    - Manage application shutdown.

    Calibration, local JSON monitoring, projection state,
    geometry transformations, rendering and command
    interpretation belong to the projection package.
    """

    def __init__(self) -> None:

        # ---------------------------------------------------------
        # Configuration
        # ---------------------------------------------------------

        self.homography_file = Path(HOMOGRAPHY_FILE)

        self.fullscreen = bool(FULLSCREEN)

        self.file_poll_interval = float(
            FILE_POLL_INTERVAL
        )

        self.gh_timeout = float(
            GH_TIMEOUT
        )

        self.frame_delay_ms = int(
            FRAME_DELAY_MS
        )

        if (
            not math.isfinite(self.file_poll_interval)
            or self.file_poll_interval <= 0.0
        ):
            raise ValueError(
                "file_poll_interval must be "
                "finite and positive."
            )

        if (
            not math.isfinite(self.gh_timeout)
            or self.gh_timeout < 0.0
        ):
            raise ValueError(
                "gh_timeout must be finite "
                "and non-negative."
            )

        if self.frame_delay_ms < 1:
            raise ValueError(
                "frame_delay_ms must be at least 1."
            )

        # ---------------------------------------------------------
        # Application lifecycle
        # ---------------------------------------------------------

        self.running = False
        self.paused = False

        # ---------------------------------------------------------
        # Projector geometry and calibration
        # ---------------------------------------------------------

        self.geometry = ProjectorGeometry.from_calibration(
            homography_file=self.homography_file,
            projector_height_mm=PROJECTOR_HEIGHT_MM,
            projector_pos_x_mm=PROJECTOR_POS_X_MM,
            projector_pos_y_mm=PROJECTOR_POS_Y_MM,
        )

        # ---------------------------------------------------------
        # Projector state and local measurement fallback
        # ---------------------------------------------------------

        self.state = ProjectorState.from_runtime(
            runtime_root=PROJECTOR_RUNTIME_ROOT,
            initial_thickness_mm=TIMBER_THICKNESS_MM,
            file_poll_interval=self.file_poll_interval,
        )

        # ---------------------------------------------------------
        # Renderer
        # ---------------------------------------------------------

        self.renderer = ProjectorRenderer(
            geometry=self.geometry,
        )

        self.renderer.offset_x_mm = float(
            PROJECTOR_OFFSET_X_MM
        )

        self.renderer.offset_y_mm = float(
            PROJECTOR_OFFSET_Y_MM
        )

        # ---------------------------------------------------------
        # Controls
        # ---------------------------------------------------------

        self.controls = ProjectorControls(
            state=self.state,
            renderer=self.renderer,
        )

        # ---------------------------------------------------------
        # Streaming
        # ---------------------------------------------------------

        self.stream_service = ProjectorStreamService()

        self.stream_started = False

        self.last_measurement_revision = 0
        self.last_geometry_revision = 0

    # -------------------------------------------------------------
    # Streaming lifecycle
    # -------------------------------------------------------------

    def _start_stream(self) -> None:
        """
        Start the projector streaming endpoint.

        If the streaming host is unavailable, continue
        operating with local measurement monitoring.
        """

        if self.stream_service is None:
            return

        try:

            self.stream_service.start()

            self.stream_started = True

            print(
                "[Projector] Streaming connected."
            )

        except (
            ConnectionError,
            OSError,
            RuntimeError,
        ) as error:

            self.stream_started = False

            print(
                "[Projector] Streaming unavailable:"
                f" {error}"
            )

            print(
                "[Projector] Continuing with local "
                "measurement monitoring."
            )

    # -------------------------------------------------------------
    # Streaming updates
    # -------------------------------------------------------------

    def _poll_stream(self) -> None:
        """
        Route the latest streaming updates to ProjectorState.

        The streaming service owns message reception
        and latest-value buffering.

        ProjectorState owns the active source and
        sensing/Grasshopper priority.
        """

        if (
            not self.stream_started
            or self.stream_service is None
        ):
            return

        # ---------------------------------------------------------
        # Sensing measurement
        # ---------------------------------------------------------

        revision, message = (
            self.stream_service.get_latest_measurement()
        )

        if (
            message is not None
            and revision != self.last_measurement_revision
        ):

            payload = message.get(
                "payload"
            )

            if isinstance(payload, dict):

                prepared = (
                    self.geometry.prepare_measurement(
                        payload
                    )
                )

                self.state.update_measurement(
                    prepared,
                    from_stream=True,
                )

                print(
                    "[Projector] Sensing stream "
                    f"revision {revision}"
                )

            self.last_measurement_revision = revision

        # ---------------------------------------------------------
        # Grasshopper geometry
        # ---------------------------------------------------------

        revision, message = (
            self.stream_service.get_latest_geometry()
        )

        if (
            message is not None
            and revision != self.last_geometry_revision
        ):

            payload = message.get(
                "payload"
            )

            source = message.get(
                "source"
            )

            if isinstance(payload, dict):

                # Explicit GH disconnect convention.
                #
                # The streaming host does not currently
                # publish automatic publisher-disconnect
                # notifications.

                if payload.get("gh_connected") is False:

                    self.state.set_disconnected()

                    print(
                        "[Projector] Grasshopper "
                        "marked disconnected."
                    )

                else:

                    prepared = (
                        self.geometry.prepare_gh_geometry(
                            payload
                        )
                    )

                    self.state.update_gh_geometry(
                        prepared,
                        source=source,
                    )

            self.last_geometry_revision = revision

    # -------------------------------------------------------------
    # Grasshopper inactivity
    # -------------------------------------------------------------

    def _check_gh_timeout(self) -> None:
        """
        Optionally restore sensing when GH stops publishing.

        Disabled by default to preserve the existing behavior.
        """

        if self.gh_timeout <= 0.0:
            return

        if self.state.check_gh_timeout(
            self.gh_timeout
        ):

            print(
                "[Projector] Grasshopper inactive "
                f"for {self.gh_timeout:.1f}s."
            )

            print(
                "[Projector] Restored latest "
                "sensing measurement."
            )

    # -------------------------------------------------------------
    # Remote commands
    # -------------------------------------------------------------

    def _process_commands(self) -> None:
        """
        Receive remote commands and delegate interpretation
        to ProjectorControls.

        The composer only executes lifecycle actions
        and sends responses through the streaming service.
        """

        if (
            not self.stream_started
            or self.stream_service is None
        ):
            return

        # Limit command processing per frame.

        for _ in range(20):

            message = (
                self.stream_service.get_command()
            )

            if message is None:
                break

            command = message.get(
                "command"
            )

            parameters = message.get(
                "parameters",
                {},
            )

            source = message.get(
                "source"
            )

            request_id = message.get(
                "request_id"
            )

            response = self.controls.handle_command(
                command=command,
                parameters=parameters,
                status=(
                    self.get_status()
                    if command == "get_status"
                    else None
                ),
            )

            # -----------------------------------------------------
            # Execute requested lifecycle action
            # -----------------------------------------------------

            if response["success"]:

                action = response.get(
                    "action"
                )

                if action == "pause":

                    self.paused = True

                elif action == "resume":

                    self.paused = False

                elif action == "stop":

                    self.running = False

            # -----------------------------------------------------
            # Return command result
            # -----------------------------------------------------

            if source and request_id:

                try:

                    self.stream_service.send_command_result(
                        target=source,
                        request_id=request_id,
                        success=response["success"],
                        result=response["result"],
                    )

                except (
                    ConnectionError,
                    OSError,
                ) as error:

                    print(
                        "[Projector] Command response "
                        f"failed: {error}"
                    )

    # -------------------------------------------------------------
    # Application status
    # -------------------------------------------------------------

    def get_status(self) -> dict:
        """
        Aggregate application, streaming and projector status.

        ProjectorState and ProjectorControls provide
        their own independent status information.
        """

        state_status = (
            self.state.get_status()
        )

        return {
            **state_status,
            "stream_connected": (
                self.stream_service.connected
                if self.stream_service is not None
                else False
            ),
            "stream_started": self.stream_started,
            "paused": self.paused,
            "fullscreen": self.fullscreen,
            "homography_file": str(
                self.homography_file
            ),
            "local_measurement_enabled": (
                not state_status[
                    "live_measurement_received"
                ]
            ),
            "controls": (
                self.controls.get_parameters()
            ),
        }

    # -------------------------------------------------------------
    # Startup information
    # -------------------------------------------------------------

    def _print_startup_info(self) -> None:

        print()
        print("=" * 60)
        print("EWOODX MODULAR PROJECTOR")
        print("=" * 60)

        print(
            "Calibration:",
            self.homography_file,
        )

        print(
            "Measurement directory:",
            PROJECTOR_RUNTIME_ROOT,
        )

        print(
            "Initial source:",
            self.state.get_active_source(),
        )

        print(
            "Streaming: enabled (local JSON fallback)"
        )

        print(
            "GH timeout:",
            (
                f"{self.gh_timeout:.1f}s"
                if self.gh_timeout > 0.0
                else "disabled"
            ),
        )

        print()
        print("Controls:")
        print("  T / t       Thickness +5 / +1 mm")
        print("  G / g       Thickness -5 / -1 mm")
        print("  0           Thickness = 0 mm")
        print("  W / S       Offset Y +/-")
        print("  A / D       Offset X -/+")
        print("  Arrow keys  Offset nudging")
        print("  + / -       Nudge step")
        print("  R           Reset offsets")
        print("  H           Toggle HUD")
        print("  Q / ESC     Exit")
        print("=" * 60)
        print()

    # -------------------------------------------------------------
    # Main application loop
    # -------------------------------------------------------------

    def run(self) -> None:
        """
        Run the projector application.

        Data and commands continue to be processed
        even when rendering is paused.
        """

        self._print_startup_info()

        self.running = True

        try:

            self._start_stream()

            self.renderer.create_window()

            if not self.fullscreen:

                cv2.setWindowProperty(
                    self.renderer.WINDOW_NAME,
                    cv2.WND_PROP_FULLSCREEN,
                    cv2.WINDOW_NORMAL,
                )

            while self.running:

                # -------------------------------------------------
                # Update projection sources
                # -------------------------------------------------

                self._poll_stream()

                self.state.poll_measurement_file()

                self._check_gh_timeout()

                # -------------------------------------------------
                # Remote commands
                # -------------------------------------------------

                self._process_commands()

                if not self.running:
                    break

                # -------------------------------------------------
                # Render current state
                # -------------------------------------------------

                if not self.paused:

                    frame = (
                        self.renderer.render_snapshot(
                            self.state.get_snapshot()
                        )
                    )

                    self.renderer.show_frame(
                        frame
                    )

                # -------------------------------------------------
                # Keyboard input
                # -------------------------------------------------

                key = self.renderer.poll_key(
                    self.frame_delay_ms
                )

                if key != -1:

                    self.running = (
                        self.controls.handle_key(
                            key
                        )
                    )

        except KeyboardInterrupt:

            print(
                "\n[Projector] Interrupted."
            )

        finally:

            self.running = False

            if self.stream_service is not None:

                self.stream_service.stop()

            self.renderer.close()

            print(
                "[Projector] Shutdown complete."
            )


# =============================================================
# APPLICATION ENTRY POINT
# =============================================================

def main() -> None:

    composer = EWoodXProjectorComposer()

    composer.run()


if __name__ == "__main__":
    main()