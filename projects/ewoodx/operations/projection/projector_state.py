"""
eWoodX - Projector State

Thread-safe state management for continuous projector operation.

Maintains two independent geometry sources:

1. Sensing measurements
   - Continuously updated by the sensing stream or runtime JSON.
   - Available for projection without Grasshopper.

2. Grasshopper geometry
   - Complete geometry payload containing timber geometry
     and additional design layers.
   - Takes priority while Grasshopper is active.

The active projection uses the latest complete Grasshopper
payload when Grasshopper is active, otherwise the latest
sensing measurement.

This module does not perform:
- TCP communication
- JSON file monitoring
- Geometry transformation
- OpenCV rendering
"""

from __future__ import annotations

import copy
import threading
import time


class ProjectorState:
    """
    Thread-safe storage for projector geometry and parameters.

    Compatible with the existing projector viewer snapshot
    interface while supporting independent sensing and GH data.
    """

    def __init__(
        self,
        initial_data: dict,
        initial_thickness_mm: float = 0.0,
    ) -> None:

        if not isinstance(initial_data, dict):
            raise TypeError(
                "initial_data must be a dictionary."
            )

        self.lock = threading.RLock()

        # ---------------------------------------------------------
        # Sensing measurement state
        # ---------------------------------------------------------

        self.measurement_data = copy.deepcopy(initial_data)

        self.measurement_revision = 0
        self.measurement_last_received_time = 0.0

        # ---------------------------------------------------------
        # Grasshopper geometry state
        # ---------------------------------------------------------

        self.gh_data = None

        self.is_connected = False
        self.last_received_time = 0.0
        self.packet_count = 0
        self.client_address = None

        # ---------------------------------------------------------
        # Projection parameters
        # ---------------------------------------------------------

        self.thickness_mm = max(
            0.0,
            float(initial_thickness_mm),
        )

        self._update_thickness(initial_data)

    # -------------------------------------------------------------
    # Internal helpers
    # -------------------------------------------------------------

    def _update_thickness(self, data: dict) -> None:
        """
        Update thickness when the payload contains a valid value.

        The existing viewer uses 'thickness_mm'.
        Sensing measurements may use 'timber_thickness_mm'.
        """

        value = data.get("thickness_mm")

        if value is None:
            value = data.get("timber_thickness_mm")

        if value is None:
            return

        try:
            value = float(value)
        except (TypeError, ValueError, OverflowError):
            return

        if value >= 0.0:
            self.thickness_mm = value

    def _gh_active(self) -> bool:
        """
        Return whether a complete GH payload is active.

        Must be called while holding self.lock.
        """

        return (
            self.is_connected
            and self.gh_data is not None
        )

    # -------------------------------------------------------------
    # Sensing measurement updates
    # -------------------------------------------------------------

    def update_measurement(
        self,
        measurement: dict,
    ) -> None:
        """
        Replace the latest sensing measurement.

        A sensing update does not overwrite stored GH geometry.

        When GH is inactive, the new sensing measurement becomes
        the active projection geometry.
        """

        if not isinstance(measurement, dict):
            raise TypeError(
                "measurement must be a dictionary."
            )

        with self.lock:

            self.measurement_data = copy.deepcopy(
                measurement
            )

            self.measurement_revision += 1

            self.measurement_last_received_time = (
                time.time()
            )

            if not self._gh_active():
                self._update_thickness(measurement)

    # -------------------------------------------------------------
    # Grasshopper geometry updates
    # -------------------------------------------------------------

    def update_gh_geometry(
        self,
        geometry: dict,
        source=None,
    ) -> None:
        """
        Replace the latest complete GH geometry payload.

        GH geometry is treated as a complete representation,
        not as an independent overlay to be merged with sensing.
        """

        if not isinstance(geometry, dict):
            raise TypeError(
                "geometry must be a dictionary."
            )

        with self.lock:

            self.gh_data = copy.deepcopy(
                geometry
            )

            self.last_received_time = time.time()

            self.packet_count += 1

            self.client_address = source

            self.is_connected = True

            self._update_thickness(geometry)

    def update_from_json(
        self,
        json_data: dict,
        client_addr=None,
    ) -> None:
        """
        Compatibility method for the existing viewer.

        The original TCP server calls update_from_json()
        whenever it receives a complete GH payload.
        """

        self.update_gh_geometry(
            geometry=json_data,
            source=client_addr,
        )

    # -------------------------------------------------------------
    # Connection state
    # -------------------------------------------------------------

    def set_disconnected(self) -> None:
        """
        Mark Grasshopper as disconnected.

        The latest sensing measurement becomes active again.
        Stored GH geometry is retained for diagnostics or
        subsequent updates, but is no longer rendered.
        """

        with self.lock:

            self.is_connected = False

            self._update_thickness(
                self.measurement_data
            )

    def set_gh_connected(
        self,
        connected: bool,
    ) -> None:
        """
        Explicitly update Grasshopper connection state.

        Connection management belongs to the composer.
        """

        with self.lock:

            self.is_connected = bool(connected)

            if not self.is_connected:
                self._update_thickness(
                    self.measurement_data
                )

    def check_gh_timeout(
        self,
        timeout_seconds: float,
    ) -> bool:
        """
        Optional freshness check.

        Returns True if GH was active but its last geometry
        update exceeded the configured timeout.

        This is not automatically invoked. The composer can
        decide whether stale data should cause a fallback.
        """

        timeout_seconds = float(timeout_seconds)

        if timeout_seconds <= 0.0:
            raise ValueError(
                "timeout_seconds must be positive."
            )

        with self.lock:

            if not self.is_connected:
                return False

            if self.last_received_time <= 0.0:
                return False

            if (
                time.time() - self.last_received_time
                > timeout_seconds
            ):

                self.is_connected = False

                self._update_thickness(
                    self.measurement_data
                )

                return True

            return False

    # -------------------------------------------------------------
    # Projection parameters
    # -------------------------------------------------------------

    def set_thickness(
        self,
        thickness_mm: float,
    ) -> None:
        """
        Set the current projector thickness manually.

        Preserves the existing viewer control interface.
        """

        value = float(thickness_mm)

        if not 0.0 <= value < float("inf"):
            raise ValueError(
                "thickness_mm must be finite and non-negative."
            )

        with self.lock:

            self.thickness_mm = value

    # -------------------------------------------------------------
    # Active geometry
    # -------------------------------------------------------------

    def get_active_source(self) -> str:
        """
        Return the currently selected geometry source.
        """

        with self.lock:

            if self._gh_active():
                return "grasshopper"

            return "sensing"

    def get_snapshot(self):
        """
        Return the existing five-element viewer snapshot.

        Returns:
            (
                active_geometry,
                gh_connected,
                gh_packet_count,
                gh_last_received_time,
                thickness_mm,
            )

        This maintains compatibility with the current
        projector rendering loop.
        """

        with self.lock:

            if self._gh_active():

                active_data = self.gh_data

            else:

                active_data = self.measurement_data

            return (
                copy.deepcopy(active_data),
                self._gh_active(),
                self.packet_count,
                self.last_received_time,
                self.thickness_mm,
            )

    # -------------------------------------------------------------
    # Individual source snapshots
    # -------------------------------------------------------------

    def get_measurement_snapshot(self) -> dict:
        """
        Return a copy of the latest sensing measurement.
        """

        with self.lock:

            return copy.deepcopy(
                self.measurement_data
            )

    def get_gh_snapshot(self) -> dict | None:
        """
        Return a copy of the latest GH geometry, if available.
        """

        with self.lock:

            return copy.deepcopy(
                self.gh_data
            )

    # -------------------------------------------------------------
    # Status
    # -------------------------------------------------------------

    def get_status(self) -> dict:
        """
        Return a thread-safe status snapshot.
        """

        with self.lock:

            return {
                "active_source": (
                    "grasshopper"
                    if self._gh_active()
                    else "sensing"
                ),
                "gh_connected": self.is_connected,
                "gh_packet_count": self.packet_count,
                "gh_last_received_time": (
                    self.last_received_time
                ),
                "gh_source": self.client_address,
                "measurement_revision": (
                    self.measurement_revision
                ),
                "measurement_last_received_time": (
                    self.measurement_last_received_time
                ),
                "thickness_mm": self.thickness_mm,
            }