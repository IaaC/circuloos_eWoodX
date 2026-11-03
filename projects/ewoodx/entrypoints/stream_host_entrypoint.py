"""
eWoodX central streaming host entrypoint.

Starts the existing EWoodXStreamHost with dedicated
sensing, projector, and controller TCP ports.

"""

import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(
    __file__
).resolve().parents[3]

sys.path.insert(
    0,
    str(PROJECT_ROOT),
)

# ---------------------------------------------------------
# Repository import path
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[3]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ---------------------------------------------------------
# Imports
# ---------------------------------------------------------

from projects.ewoodx.config import (
    STREAM_BIND_HOST,
    SENSING_STREAM_PORT,
    PROJECTOR_STREAM_PORT,
    CONTROLLER_STREAM_PORT,
)

from projects.ewoodx.operations.streaming.stream_host import (
    EWoodXStreamHost,
)


# ---------------------------------------------------------
# Host entrypoint
# ---------------------------------------------------------

def main() -> None:
    """
    Start and maintain the central eWoodX stream host.
    """

    print()
    print("=" * 60)
    print("eWoodX CENTRAL STREAM HOST")
    print("=" * 60)

    print()
    print("[eWoodX] Stream configuration:")
    print(f"  Bind host       : {STREAM_BIND_HOST}")
    print(f"  Sensing port    : {SENSING_STREAM_PORT}")
    print(f"  Projector port  : {PROJECTOR_STREAM_PORT}")
    print(f"  Controller port : {CONTROLLER_STREAM_PORT}")

    host = EWoodXStreamHost(
        host=STREAM_BIND_HOST,
        sensing_port=SENSING_STREAM_PORT,
        projector_port=PROJECTOR_STREAM_PORT,
        controller_port=CONTROLLER_STREAM_PORT,
    )

    started = False

    try:
        print()
        print("[eWoodX] Starting stream host...")

        host.start()
        started = True

        print()
        print("[eWoodX] Stream host started successfully.")
        print("[eWoodX] Waiting for agent connections.")
        print("[eWoodX] Press Ctrl+C to stop.")

        print()
        print("=" * 60)

        # Monitor registered agents without modifying the host.
        previous_agents = {}

        while True:
            current_agents = host.connected_agents

            # Newly registered agents
            for agent_id, channel in current_agents.items():
                if agent_id not in previous_agents:
                    print(
                        f"[eWoodX] Agent connected: "
                        f"{agent_id} ({channel})",
                        flush=True,
                    )

            # Disconnected agents
            for agent_id, channel in previous_agents.items():
                if agent_id not in current_agents:
                    print(
                        f"[eWoodX] Agent disconnected: "
                        f"{agent_id} ({channel})",
                        flush=True,
                    )

            previous_agents = current_agents.copy()

            time.sleep(0.5)

    except KeyboardInterrupt:
        print()
        print("[eWoodX] Shutdown requested.")

    except Exception as error:
        print()
        print("[eWoodX] Stream host error:")
        print(f"  {type(error).__name__}: {error}")
        raise

    finally:
        if started:
            print()
            print("[eWoodX] Stopping stream host...")
            host.stop()
            print("[eWoodX] Stream host stopped.")

        print("=" * 60)


if __name__ == "__main__":
    main()