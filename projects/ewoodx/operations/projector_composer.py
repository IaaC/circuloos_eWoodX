
"""
eWoodX - Projector Composer

Main application for the modular eWoodX projection system.

Coordinates:
- ProjectorState
- ProjectorGeometry
- ProjectorRenderer
- ProjectorControls
- ProjectorStreamService

Sources:
1. Local timber measurement JSON
2. Live sensing measurement stream
3. Complete Grasshopper geometry stream

Grasshopper geometry takes priority while active.
The latest sensing measurement remains independently stored.

The legacy projector_live_viewer.py is not imported.

Run from repository root:

    python -m projects.ewoodx.operations.projector_composer

Optional:
    --no-stream
    --windowed
    --gh-timeout 5
    --file-poll 0.5
    --homography PATH
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import cv2
import numpy as np

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


class EWoodXProjectorComposer:
    """
    Main coordinator for the modular projector application.

    Streaming callbacks only update the stream service's
    latest-value buffers. The composer processes those buffers
    in the main application loop.
    """

    def __init__(
        self,
        homography_file: Path | None = None,
        use_stream: bool = True,
        fullscreen: bool = True,
        file_poll_interval: float = 0.5,
        gh_timeout: float = 0.0,
        frame_delay_ms: int = 16,
    ) -> None:

        self.homography_file = (
            Path(homography_file)
            if homography_file is not None
            else (
                CALIBRATION_ROOT
                / "projector"
                / PROJECTOR_CALIBRATION_MODE
                / "projector_homography.npz"
            )
        )

        self.use_stream = bool(use_stream)
        self.fullscreen = bool(fullscreen)

        self.file_poll_interval = float(
            file_poll_interval
        )

        self.gh_timeout = float(gh_timeout)
        self.frame_delay_ms = int(frame_delay_ms)

        if self.file_poll_interval <= 0:
            raise ValueError(
                "file_poll_interval must be positive."
            )

        if self.gh_timeout < 0:
            raise ValueError(
                "gh_timeout cannot be negative."
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

        self.stream_service = None
        self.stream_started = False

        self.last_measurement_revision = 0
        self.last_geometry_revision = 0

        # ---------------------------------------------------------
        # Local measurement monitoring
        # ---------------------------------------------------------

        self.last_file_check = 0.0
        self.last_file_signature = None

        # Once a live sensing measurement is received,
        # it takes priority over local JSON polling.
        self.live_measurement_received = False

        # ---------------------------------------------------------
        # Calibration
        # ---------------------------------------------------------

        homography = self._load_homography()

        self.geometry = ProjectorGeometry(
            homography=homography,
            projector_height_mm=PROJECTOR_HEIGHT_MM,
            projector_pos_x_mm=PROJECTOR_POS_X_MM,
            projector_pos_y_mm=PROJECTOR_POS_Y_MM,
        )

        # ---------------------------------------------------------
        # Initial sensing measurement
        # ---------------------------------------------------------

        initial_data = self._load_initial_measurement()

        self.state = ProjectorState(
            initial_data=self.geometry.prepare_measurement(
                initial_data
            ),
            initial_thickness_mm=TIMBER_THICKNESS_MM,
        )

        # ---------------------------------------------------------
        # Renderer and controls
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

        self.controls = ProjectorControls(
            state=self.state,
            renderer=self.renderer,
        )

        # ---------------------------------------------------------
        # Streaming
        # ---------------------------------------------------------

        if self.use_stream:
            self.stream_service = (
                ProjectorStreamService()
            )

    # -------------------------------------------------------------
    # Calibration
    # -------------------------------------------------------------

    def _load_homography(self) -> np.ndarray:

        if not self.homography_file.exists():

            print(
                "[Projector] Calibration not found:"
            )
            print(
                f"  {self.homography_file}"
            )
            print(
                "[Projector] Using identity homography "
                "for testing."
            )

            return np.eye(
                3,
                dtype=np.float32,
            )

        with np.load(
            self.homography_file,
            allow_pickle=True,
        ) as calibration:

            homography = np.asarray(
                calibration["H_world_to_projector"],
                dtype=np.float32,
            )

        if homography.shape != (3, 3):
            raise ValueError(
                "Calibration homography must be 3x3."
            )

        if not np.all(np.isfinite(homography)):
            raise ValueError(
                "Calibration homography contains "
                "non-finite values."
            )

        print(
            "[Projector] Calibration loaded:"
        )
        print(
            f"  {self.homography_file}"
        )

        return homography

    # -------------------------------------------------------------
    # Local measurement files
    # -------------------------------------------------------------

    @staticmethod
    def _empty_measurement() -> dict:

        return {
            "source": "None",
            "timber_id": 1,
            "length_mm": 0.0,
            "width_mm": 0.0,
            "thickness_mm": 0.0,
            "contour_mm": [],
            "corners_mm": [],
            "defects": [],
            "cut_geo": [],
            "mill_geo": [],
            "points_geo": [],
            "labels": [],
        }

    @staticmethod
    def _measurement_files():

        return list(
            PROJECTOR_RUNTIME_ROOT.glob(
                "timber_*_measurement.json"
            )
        )

    def _latest_measurement_file(self):

        files = self._measurement_files()

        if not files:
            return None

        return max(
            files,
            key=lambda path: path.stat().st_mtime_ns,
        )

    @staticmethod
    def _file_signature(path: Path):

        stat = path.stat()

        return (
            str(path.resolve()),
            stat.st_mtime_ns,
            stat.st_size,
        )

    @staticmethod
    def _read_measurement_file(
        path: Path,
    ) -> dict:

        with path.open(
            "r",
            encoding="utf-8",
        ) as handle:

            data = json.load(handle)

        if not isinstance(data, dict):
            raise ValueError(
                "Measurement JSON must contain "
                "a dictionary."
            )

        # Preserve the original projector's sensing
        # measurement schema and fallback fields.

        return {
            "source": path.name,
            "timber_id": data.get(
                "timber_id",
                1,
            ),
            "length_mm": data.get(
                "length_mm",
                0.0,
            ),
            "width_mm": data.get(
                "width_mm",
                0.0,
            ),
            "thickness_mm": data.get(
                "thickness_mm",
                data.get(
                    "timber_thickness_mm",
                    TIMBER_THICKNESS_MM,
                ),
            ),
            "contour_mm": data.get(
                "contour_mm",
                [],
            ),
            "corners_mm": data.get(
                "corners_mm",
                [],
            ),
            "defects": data.get(
                "defects",
                [],
            ),
            "cut_geo": [],
            "mill_geo": [],
            "points_geo": [],
            "labels": [],
        }

    def _load_initial_measurement(self) -> dict:

        try:

            path = self._latest_measurement_file()

            if path is None:

                print(
                    "[Projector] No local timber "
                    "measurement found."
                )

                return self._empty_measurement()

            data = self._read_measurement_file(
                path
            )

            self.last_file_signature = (
                self._file_signature(path)
            )

            print(
                "[Projector] Initial measurement:"
            )
            print(
                f"  {path.name}"
            )

            return data

        except (
            OSError,
            ValueError,
            TypeError,
        ) as error:

            print(
                "[Projector] Initial measurement "
                f"load failed: {error}"
            )

            return self._empty_measurement()

    def _poll_measurement_file(self) -> None:
        """
        Check for new or modified local measurement JSON.

        Once a live sensing stream has delivered a measurement,
        the stream remains the preferred sensing source.
        """

        if self.live_measurement_received:
            return

        now = time.monotonic()

        if (
            now - self.last_file_check
            < self.file_poll_interval
        ):
            return

        self.last_file_check = now

        try:

            path = self._latest_measurement_file()

            if path is None:
                return

            signature = self._file_signature(
                path
            )

            if signature == self.last_file_signature:
                return

            data = self._read_measurement_file(
                path
            )

            prepared = (
                self.geometry.prepare_measurement(
                    data
                )
            )

            self.state.update_measurement(
                prepared
            )

            self.last_file_signature = signature

            print(
                "[Projector] Local measurement updated:"
                f" {path.name}"
            )

        except (
            OSError,
            ValueError,
            TypeError,
        ) as error:

            print(
                "[Projector] Local measurement "
                f"update failed: {error}"
            )

    # -------------------------------------------------------------
    # Streaming
    # -------------------------------------------------------------

    def _start_stream(self) -> None:

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

            print(
                "[Projector] Streaming unavailable:"
                f" {error}"
            )

            print(
                "[Projector] Continuing with local "
                "measurement monitoring."
            )

    def _poll_stream(self) -> None:

        if (
            not self.stream_started
            or self.stream_service is None
        ):
            return

        # ---------------------------------------------------------
        # Sensing measurement
        # ---------------------------------------------------------

        revision, message = (
            self.stream_service
            .get_latest_measurement()
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
                    prepared
                )

                self.live_measurement_received = True

                print(
                    "[Projector] Sensing stream "
                    f"revision {revision}"
                )

            self.last_measurement_revision = revision

        # ---------------------------------------------------------
        # Grasshopper / complete projector geometry
        # ---------------------------------------------------------

        revision, message = (
            self.stream_service
            .get_latest_geometry()
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

                # Explicit disconnect message.
                #
                # This is a composer-level convention.
                # The streaming framework itself does not
                # currently emit publisher disconnect events.

                if payload.get(
                    "gh_connected"
                ) is False:

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
    # Optional Grasshopper inactivity timeout
    # -------------------------------------------------------------

    def _check_gh_timeout(self) -> None:

        if self.gh_timeout <= 0:
            return

        timed_out = self.state.check_gh_timeout(
            self.gh_timeout
        )

        if timed_out:

            print(
                "[Projector] Grasshopper inactive "
                f"for {self.gh_timeout:.1f}s."
            )

            print(
                "[Projector] Restored latest "
                "sensing measurement."
            )

    # -------------------------------------------------------------
    # Stream commands
    # -------------------------------------------------------------

    def _process_commands(self) -> None:

        if (
            not self.stream_started
            or self.stream_service is None
        ):
            return

        # Bound work per frame so incoming commands cannot
        # indefinitely delay the rendering loop.

        for _ in range(20):

            message = (
                self.stream_service.get_command()
            )

            if message is None:
                break

            command = message.get("command")
            parameters = message.get(
                "parameters",
                {},
            )

            source = message.get("source")
            request_id = message.get("request_id")

            success = True
            result = {}

            try:

                if command == "get_status":

                    result = self.get_status()

                elif command == "set_thickness":

                    value = float(
                        parameters["thickness_mm"]
                    )

                    self.state.set_thickness(
                        value
                    )

                    result = {
                        "thickness_mm": value,
                    }

                elif command == "pause":

                    self.paused = True

                    result = {
                        "paused": True,
                    }

                elif command == "resume":

                    self.paused = False

                    result = {
                        "paused": False,
                    }

                elif command == "stop":

                    self.running = False

                    result = {
                        "stopping": True,
                    }

                else:

                    success = False

                    result = {
                        "error": (
                            "Unsupported projector command: "
                            f"{command}"
                        )
                    }

            except (
                KeyError,
                TypeError,
                ValueError,
            ) as error:

                success = False

                result = {
                    "error": str(error),
                }

            if source and request_id:

                try:

                    self.stream_service.send_command_result(
                        target=source,
                        request_id=request_id,
                        success=success,
                        result=result,
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
    # Status
    # -------------------------------------------------------------

    def get_status(self) -> dict:

        return {
            **self.state.get_status(),
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
                not self.live_measurement_received
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
            "Streaming:",
            "enabled" if self.use_stream else "disabled",
        )

        print(
            "GH timeout:",
            (
                f"{self.gh_timeout:.1f}s"
                if self.gh_timeout > 0
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
    # Main loop
    # -------------------------------------------------------------

    def run(self) -> None:

        self._print_startup_info()

        self.running = True

        try:

            if self.use_stream:
                self._start_stream()

            self.renderer.create_window()

            if not self.fullscreen:

                cv2.setWindowProperty(
                    self.renderer.WINDOW_NAME,
                    cv2.WND_PROP_FULLSCREEN,
                    cv2.WINDOW_NORMAL,
                )

            while self.running:

                # Always process incoming data, even while
                # projection rendering is paused.

                self._poll_stream()

                self._poll_measurement_file()

                self._process_commands()

                self._check_gh_timeout()

                if not self.paused:

                    snapshot = (
                        self.state.get_snapshot()
                    )

                    frame = (
                        self.renderer.render_snapshot(
                            snapshot
                        )
                    )

                    self.renderer.show_frame(
                        frame
                    )

                key = self.renderer.poll_key(
                    self.frame_delay_ms
                )

                if key != -1:

                    self.running = (
                        self.controls.handle_key(key)
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


# -------------------------------------------------------------
# Command-line entry point
# -------------------------------------------------------------

def main() -> None:

    parser = argparse.ArgumentParser(
        description=(
            "eWoodX modular projector composer"
        ),
    )

    parser.add_argument(
        "--homography",
        type=Path,
        default=None,
        help="Path to projector homography NPZ.",
    )

    parser.add_argument(
        "--no-stream",
        action="store_true",
        help="Run without the streaming service.",
    )

    parser.add_argument(
        "--windowed",
        action="store_true",
        help="Disable fullscreen projector display.",
    )

    parser.add_argument(
        "--file-poll",
        type=float,
        default=0.5,
        help=(
            "Local measurement file polling "
            "interval in seconds."
        ),
    )

    parser.add_argument(
        "--gh-timeout",
        type=float,
        default=0.0,
        help=(
            "Optional Grasshopper inactivity "
            "timeout in seconds. "
            "0 disables timeout."
        ),
    )

    parser.add_argument(
        "--frame-delay",
        type=int,
        default=16,
        help=(
            "OpenCV keyboard polling delay "
            "in milliseconds."
        ),
    )

    args = parser.parse_args()

    composer = EWoodXProjectorComposer(
        homography_file=args.homography,
        use_stream=not args.no_stream,
        fullscreen=not args.windowed,
        file_poll_interval=args.file_poll,
        gh_timeout=args.gh_timeout,
        frame_delay_ms=args.frame_delay,
    )

    composer.run()


if __name__ == "__main__":
    main()