# eWoodX Configuration

The `projects.ewoodx.config` package centralizes project-specific configuration used by the eWoodX application layer.

It defines the current configuration for:

- workspace organization;
- sensing equipment and calibration;
- Timber entity identity and indexing;
- distributed communication;
- projection.

These values configure how eWoodX composes and uses the reusable framework. They are therefore intentionally located in the **project layer** rather than in the generic `framework` package.

The project and its configuration are under **continuous development**. The values and configuration groups documented here describe the current implementation and may evolve as additional equipment, agents, operations, and workflows are integrated.

---

# Package Structure

```text
projects/ewoodx/config/
├── __init__.py
├── workspace.py
├── sensing.py
├── entity.py
├── communication.py
└── projection.py
```

The responsibilities are divided as follows:

| Module | Responsibility |
|---|---|
| `workspace.py` | Project paths, workspace layout, domain names, and entry naming. |
| `sensing.py` | Physical sensing workspace, camera configuration, calibration, and Timber segmentation parameters. |
| `entity.py` | Timber entity type, ID generation parameters, and indexed metadata schema. |
| `communication.py` | Master and sensing-agent runtime/network configuration. |
| `projection.py` | Projector geometry, display configuration, calibration, and temporary projector runtime compatibility. |
| `__init__.py` | Re-exports the intended public project configuration. |

---

# Architectural Role

The configuration package sits between the project implementation and the generic framework.

```text
projects.ewoodx
      │
      ├── agents
      ├── entrypoints
      ├── operations
      └── orchestration
             │
             ▼
           config
             │
             ▼
     project-specific values
             │
             ▼
          framework
```

For example, the generic communication framework provides reusable `Agent`, `TCPServer`, `ActionStore`, and workflow components.

The eWoodX configuration determines project-specific values such as:

```text
master port
sensing agent ID
sensing role
runtime directory
polling interval
```

Similarly, the generic sensing framework provides reusable camera and calibration classes, while this package determines the actual camera indices, resolutions, calibration parameters, and physical dimensions used by eWoodX.

The distinction is:

```text
framework
    │
    └── reusable mechanism

projects.ewoodx.config
    │
    └── project-specific configuration
```

---

# Public Configuration API

The intended package-level configuration API is re-exported through:

```python
projects.ewoodx.config
```

For example:

```python
from projects.ewoodx.config import (
    EWOODX_REPOSITORY_ROOT,
    EWOODX_WORKSPACE_LAYOUT,
    TIMBER_ENTITY_TYPE,
    TIMBER_ENTITY_INDEX,
    MASTER_HOST,
    MASTER_PORT,
    SENSING_AGENT_ID,
    ANGETUBE_CAMERA_INDEX,
)
```

The package-level exports are organized into five configuration groups:

```text
Workspace
Sensing
Entity
Communication
Projection
```

Application modules should normally import these public configuration values rather than reproduce the same constants locally.

---

# Workspace Configuration

Defined in:

```text
workspace.py
```

This module establishes the project filesystem context and how eWoodX uses the generic workspace framework.

## Project Paths

### `EWOODX_PROJECT_ROOT`

Path to:

```text
projects/ewoodx/
```

It is derived from the location of `workspace.py`.

### `EWOODX_REPOSITORY_ROOT`

Path to the repository root.

It is derived from `EWOODX_PROJECT_ROOT`.

These paths allow other project configuration to construct locations without relying on the process working directory.

---

# Workspace Layout

### `EWOODX_WORKSPACE_LAYOUT`

Current value:

```python
{
    "index": "index",
    "sensing": "sensing",
    "design": "design",
    "robot_control": "robot_control",
}
```

This defines the eWoodX-specific layout supplied to the generic workspace framework.

Conceptually:

```text
Workspace
    │
    ├── index
    ├── sensing
    ├── design
    └── robot_control
```

These names are project semantics. They are not requirements imposed by `framework.workspace`.

---

# Workspace Domains

The project currently defines three domain names:

```python
SENSING_DOMAIN = "sensing"
DESIGN_DOMAIN = "design"
ROBOT_CONTROL_DOMAIN = "robot_control"
```

They identify the main operational areas anticipated by the project.

Their presence in configuration does not imply that all three areas currently have the same level of implementation maturity.

---

# Entry Naming

Current entry naming configuration:

```python
ENTRY_NAME_PREFIX = "day"
ENTRY_DATE_FORMAT = "%Y%m%d"
```

These values support date-based project entry naming.

For example, an application can construct names following the pattern:

```text
dayYYYYMMDD
```

The actual creation and management of entries remains the responsibility of the workspace/application logic.

---

# Sensing Configuration

Defined in:

```text
sensing.py
```

This module contains the project-specific physical and camera configuration used by current sensing operations.

It configures:

```text
calibration storage
physical workspace dimensions
Arducam
Angetube webcam
Timber segmentation
measurement geometry
```

---

# Calibration Root

### `CALIBRATION_ROOT`

Calibration data is rooted at:

```text
projects/ewoodx/calibration_data/
```

through:

```python
CALIBRATION_ROOT = EWOODX_PROJECT_ROOT / "calibration_data"
```

Camera-specific calibration layouts are defined relative to this location.

---

# Physical Sensing Workspace

The current physical table dimensions are:

```python
TABLE_WIDTH_MM = 1780.0
TABLE_HEIGHT_MM = 1040.0
```

Units are millimetres.

These dimensions are used by the current planar camera calibration configuration.

---

# Arducam Acquisition

Current acquisition configuration:

```python
ARDUCAM_CAMERA_INDEX = 1

ARDUCAM_IMAGE_WIDTH = 1280
ARDUCAM_IMAGE_HEIGHT = 720
```

These values are passed into the reusable Arducam sensing implementation.

---

# Arducam Intrinsic Calibration

Current checkerboard configuration:

```python
ARDUCAM_CHECKERBOARD_INNER_CORNERS = (13, 8)

ARDUCAM_CHECKERBOARD_SQUARE_SIZE_MM = 20.0
```

The Arducam implementation currently uses the standard pinhole intrinsic calibration provided by the sensing framework.

---

# Arducam Calibration Layout

```python
ARDUCAM_CALIBRATION_LAYOUT = {
    "intrinsic": "arducam/intrinsic",
    "intrinsic_images": "arducam/intrinsic/images",
    "extrinsic": "arducam/extrinsic",
    "extrinsic_images": "arducam/extrinsic/images",
}
```

These paths organize the different calibration artifacts beneath the project calibration root.

Conceptually:

```text
calibration_data/
└── arducam/
    ├── intrinsic/
    │   └── images/
    └── extrinsic/
        └── images/
```

---

# Arducam Planar Calibration

The current ArUco dictionary is:

```python
ARDUCAM_ARUCO_DICTIONARY = "DICT_4X4_50"
```

Marker size:

```python
ARDUCAM_MARKER_SIZE_MM = 100.0
```

The physical marker positions are:

```python
{
    1: (0.0, 0.0),
    0: (TABLE_WIDTH_MM, 0.0),
    2: (0.0, TABLE_HEIGHT_MM),
    3: (TABLE_WIDTH_MM, TABLE_HEIGHT_MM),
}
```

The configured outer-corner mapping is:

```python
{
    0: 0,
    1: 1,
    2: 2,
    3: 3,
}
```

These values provide the project-specific physical interpretation of ArUco detections.

This distinction is important:

```text
framework.sensing
      │
      └── detects marker IDs and image coordinates

projects.ewoodx.config
      │
      └── assigns physical marker positions
```

The physical marker arrangement is therefore an eWoodX configuration rather than a generic camera assumption.

---

# Arducam Measurement Setup

Current camera height:

```python
ARDUCAM_CAMERA_HEIGHT_MM = 1750.0
```

Units are millimetres.

This value belongs to the current project measurement setup rather than to the reusable Arducam camera implementation.

---

# Angetube Acquisition

Current acquisition configuration:

```python
ANGETUBE_CAMERA_INDEX = 0

ANGETUBE_IMAGE_WIDTH = 3840
ANGETUBE_IMAGE_HEIGHT = 2160

ANGETUBE_CAMERA_FPS = 30

ANGETUBE_CAMERA_FOURCC = "MJPG"
```

These values configure the current Angetube webcam stream.

---

# Angetube Camera Control

The current camera-property configuration is:

```python
ANGETUBE_FOCUS_MODE = "manual"
ANGETUBE_FOCUS_VALUE = 380

ANGETUBE_EXPOSURE_MODE = "auto"
ANGETUBE_EXPOSURE_VALUE = -5

ANGETUBE_BRIGHTNESS = 9
ANGETUBE_CONTRAST = 32
ANGETUBE_SATURATION = 32
ANGETUBE_SHARPNESS = 32
ANGETUBE_GAIN = 0
ANGETUBE_BACKLIGHT_COMPENSATION = 0

ANGETUBE_WHITE_BALANCE_MODE = "auto"
ANGETUBE_WHITE_BALANCE_TEMPERATURE = 5000

ANGETUBE_DIGITAL_ZOOM = 2.00
```

These are project-selected values supplied to the reusable `AngetubeCamera`.

Some properties may depend on camera, driver, operating system, or backend support. The sensing framework handles the device-level application of supported properties.

---

# Angetube Intrinsic Calibration

Current checkerboard configuration:

```python
ANGETUBE_CHECKERBOARD_INNER_CORNERS = (13, 8)

ANGETUBE_CHECKERBOARD_SQUARE_SIZE_MM = 20.0
```

Current calibration model:

```python
ANGETUBE_CALIBRATION_MODEL = "fisheye"
```

Fisheye configuration:

```python
ANGETUBE_FISHEYE_BALANCE = 0.0
ANGETUBE_FISHEYE_FOV_SCALE = 1.0

ANGETUBE_FISHEYE_CHECK_COND = True
ANGETUBE_FISHEYE_RECOMPUTE_EXTRINSIC = True
ANGETUBE_FISHEYE_FIX_SKEW = True
```

These configure the generic Angetube intrinsic calibration implementation for the current eWoodX camera setup.

---

# Angetube Calibration Layout

```python
ANGETUBE_CALIBRATION_LAYOUT = {
    "intrinsic": "webcam_angetube/intrinsic",
    "intrinsic_images": "webcam_angetube/intrinsic/images",
    "extrinsic": "webcam_angetube/extrinsic",
    "extrinsic_images": "webcam_angetube/extrinsic/images",
}
```

Conceptually:

```text
calibration_data/
└── webcam_angetube/
    ├── intrinsic/
    │   └── images/
    └── extrinsic/
        └── images/
```

---

# Angetube Planar Calibration

Current ArUco dictionary:

```python
ANGETUBE_ARUCO_DICTIONARY = "DICT_4X4_50"
```

Marker size:

```python
ANGETUBE_MARKER_SIZE_MM = 150.0
```

Physical marker positions:

```python
{
    1: (0.0, 0.0),
    0: (TABLE_WIDTH_MM, 0.0),
    2: (0.0, TABLE_HEIGHT_MM),
    3: (TABLE_WIDTH_MM, TABLE_HEIGHT_MM),
}
```

Outer-corner mapping:

```python
{
    0: 0,
    1: 1,
    2: 2,
    3: 3,
}
```

As with the Arducam configuration, these physical coordinates belong to the eWoodX application layer.

---

# Angetube Measurement Setup

Current camera height:

```python
ANGETUBE_CAMERA_HEIGHT_MM = 1620.0
```

Units are millimetres.

---

# Timber Segmentation Configuration

The current Timber segmentation parameters are:

```python
TIMBER_MIN_CONTOUR_AREA_PX = 5000

TIMBER_CONTOUR_APPROX_FACTOR = 0.004

TIMBER_THICKNESS_MM = 0.0
```

These are application-specific sensing parameters.

They do not belong to the generic camera framework because they describe how eWoodX interprets acquired imagery as Timber geometry rather than how the camera itself operates.

The boundary is:

```text
camera acquisition / calibration
        │
        ▼
framework.sensing
```

versus:

```text
Timber segmentation / measurement
        │
        ▼
projects.ewoodx
```

---

# Entity Configuration

Defined in:

```text
entity.py
```

This module defines how the current application represents and indexes persistent Timber entities.

---

# Timber Entity Type

```python
TIMBER_ENTITY_TYPE = "timber"
```

This is an application-specific entity type used with the generic `EntityManager`.

The generic workspace framework does not define Timber as an entity type.

---

# Timber Entity IDs

Current ID configuration:

```python
TIMBER_ID_PREFIX = "T"

ENTITY_ID_SEQUENCE_MIN_WIDTH = 4
ENTITY_ID_SEQUENCE_MAX_VALUE = 999999

ENTITY_ID_RANDOM_LENGTH = 3

ENTITY_ID_RANDOM_ALPHABET = (
    "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
)
```

These values configure the current Timber identifier scheme used by the project.

They define project identity conventions rather than generic entity-management behavior.

---

# Timber Entity Index

The current indexed Timber metadata schema is:

```python
TIMBER_ENTITY_INDEX = {
    "color": "TEXT",
    "length_mm": "REAL",
    "width_mm": "REAL",
    "thickness_mm": "REAL",
    "area_mm2": "REAL",
}
```

These properties are registered in the workspace-level entity index and can therefore participate in indexed entity queries.

The current indexed fields are:

| Property | SQLite type | Meaning |
|---|---|---|
| `color` | `TEXT` | Timber color classification/value. |
| `length_mm` | `REAL` | Timber length in millimetres. |
| `width_mm` | `REAL` | Timber width in millimetres. |
| `thickness_mm` | `REAL` | Timber thickness in millimetres. |
| `area_mm2` | `REAL` | Timber area in square millimetres. |

The schema is intentionally project-specific:

```text
framework.workspace.EntityManager
        │
        └── generic indexed entity mechanism

TIMBER_ENTITY_INDEX
        │
        └── eWoodX indexed properties
```

---

# Communication Configuration

Defined in:

```text
communication.py
```

This module configures the current distributed eWoodX deployment.

---

# Agent Runtime Storage

### `AGENTS_RUNTIME_ROOT`

Current runtime state root:

```text
<repository>/agents_runtime/
```

defined by:

```python
AGENTS_RUNTIME_ROOT = (
    EWOODX_REPOSITORY_ROOT
    / "agents_runtime"
)
```

The master and deployed agents use locations beneath this root for their persistent communication/execution state.

---

# Master Configuration

Current master configuration:

```python
MASTER_BIND_HOST = "0.0.0.0"

MASTER_HOST = "127.0.0.1"

MASTER_PORT = 5105

MASTER_FILE_PORT = 5106
```

The distinction between the host values is important.

### `MASTER_BIND_HOST`

Used by the master server when binding its listening interface.

Current value:

```text
0.0.0.0
```

### `MASTER_HOST`

Used by clients when connecting to the master.

Current value:

```text
127.0.0.1
```

### `MASTER_PORT`

Current command/workflow API port:

```text
5105
```

### `MASTER_FILE_PORT`

Current file-transfer API port:

```text
5106
```

Command communication and raw file transfer therefore use separate services.

---

# Sensing Agent Configuration

Current sensing agent identity:

```python
SENSING_AGENT_ID = "sensing_pc_01"
```

Current roles:

```python
SENSING_AGENT_ROLES = [
    "sensing",
]
```

The role determines which distributed actions the agent is eligible to claim.

Current local API configuration:

```python
SENSING_AGENT_HOST = "127.0.0.1"

SENSING_AGENT_PORT = 6105
```

Current polling interval:

```python
SENSING_AGENT_POLL_INTERVAL = 1.0
```

The interval is expressed in seconds.

Conceptually:

```text
Master
127.0.0.1:5105
      ▲
      │ polling / workflow
      │
Sensing Agent
sensing_pc_01
role: sensing
      ▲
      │ local API
      │
127.0.0.1:6105
```

These are the current deployment values and may change when agents are deployed across different machines or network configurations.

---

# Projection Configuration

Defined in:

```text
projection.py
```

This module configures the current projector setup.

It contains:

```text
physical projector position
display resolution
screen origin
environment-specific resolution
command-line overrides
fine adjustment
calibration directories
temporary compatibility runtime
```

---

# Projector Physical Setup

Current physical configuration:

```python
PROJECTOR_HEIGHT_MM = 2300.0

PROJECTOR_POS_X_MM = 920.0
PROJECTOR_POS_Y_MM = 50.0
```

Units are millimetres.

---

# Projector Display

Default display configuration:

```python
PROJECTOR_WIDTH = 1280
PROJECTOR_HEIGHT = 800

PROJECTOR_SCREEN_ORIGIN_X = 2560
PROJECTOR_SCREEN_ORIGIN_Y = 0
```

The screen-origin values determine the display-space position used by the current projector workflow.

---

# Projector Environment

The projector configuration reads:

```text
EWOODX_ENV
```

from the environment.

The default is:

```text
development
```

Current environment-specific resolutions are:

### Development

```python
PROJECTOR_WIDTH = 1280
PROJECTOR_HEIGHT = 800
```

### Production

```python
PROJECTOR_WIDTH = 1920
PROJECTOR_HEIGHT = 1080
```

If `EWOODX_ENV` contains another value, the default display values defined earlier in the module remain in effect.

---

# Projector Command-Line Overrides

The current projection configuration recognizes:

```text
--proj_width
--proj_height
--proj_x
--proj_y
```

These can override:

```text
PROJECTOR_WIDTH
PROJECTOR_HEIGHT
PROJECTOR_SCREEN_ORIGIN_X
PROJECTOR_SCREEN_ORIGIN_Y
```

at import time.

For example:

```bash
python <projection_application>.py \
    --proj_width 1920 \
    --proj_height 1080 \
    --proj_x 1920 \
    --proj_y 0
```

The projection module uses `parse_known_args()`, allowing these projector arguments to coexist with other command-line arguments.

---

# Projector Fine Adjustment

Current physical offsets:

```python
PROJECTOR_OFFSET_X_MM = 0.0
PROJECTOR_OFFSET_Y_MM = 0.0
```

These provide project-level fine adjustment in millimetres.

---

# Projector Calibration Mode

Current mode:

```python
PROJECTOR_CALIBRATION_MODE = "manual"
```

---

# Projector Calibration Layout

```python
PROJECTOR_CALIBRATION_LAYOUT = {
    "manual": "projector/manual",
    "automatic": "projector/automatic",
}
```

These paths organize projector calibration data relative to the project calibration root.

Conceptually:

```text
calibration_data/
└── projector/
    ├── manual/
    └── automatic/
```

---

# Temporary Projector Runtime

### `PROJECTOR_RUNTIME_ROOT`

Current location:

```text
<repository>/projector_runtime/
```

This directory is a **temporary compatibility mechanism** for the current projector workflow.

Current sensing operations can write a compatibility copy of Timber measurement data using files following the pattern:

```text
timber_*_measurement.json
```

The intended relationship is:

```text
Persistent Timber Entity
        │
        ├── authoritative data
        │
        └── temporary copy
                │
                ▼
        projector_runtime/
                │
                ▼
        current projector workflow
```

The persistent Timber entity remains the authoritative source.

This compatibility directory is expected to be removed or replaced when the design/data workflow retrieves the required entity data through the database and distributed communication workflow.

> **Development note:** `PROJECTOR_RUNTIME_ROOT` should not be treated as the long-term authoritative data architecture.

---

# Configuration Dependency Structure

The current configuration modules have a small dependency structure.

```text
workspace.py
    │
    ├──────────────► sensing.py
    │
    ├──────────────► communication.py
    │
    └──────────────► projection.py
                         ▲
                         │
                     sensing.py

entity.py
    │
    └── independent project entity configuration
```

More specifically:

```text
workspace.py
    └── project/repository paths

sensing.py
    ├── uses project root
    └── defines table dimensions

communication.py
    └── uses repository root

projection.py
    ├── uses repository root
    └── uses sensing table dimensions
```

This allows shared physical and filesystem configuration to remain defined in one place.

---

# Configuration vs Framework Defaults

Project configuration should not be confused with generic framework behavior.

For example:

```text
Agent supports roles
        │
        ▼
framework.communication
```

while:

```text
"sensing" is an agent role
        │
        ▼
projects.ewoodx.config
```

Similarly:

```text
EntityManager supports indexed properties
        │
        ▼
framework.workspace
```

while:

```text
length_mm and width_mm are indexed
Timber properties
        │
        ▼
projects.ewoodx.config
```

And:

```text
AngetubeCamera supports configurable
camera properties
        │
        ▼
framework.sensing
```

while:

```text
focus_value = 380
digital_zoom = 2.0
        │
        ▼
projects.ewoodx.config
```

The generic framework defines capability.

The project configuration selects how that capability is currently used.

---

# Units

Physical dimensions currently follow these conventions:

```text
physical length / position / height → millimetres
area                               → square millimetres
image dimensions                   → pixels
contour area threshold             → pixels²
poll interval                      → seconds
```

Property names generally include their units where appropriate:

```text
length_mm
width_mm
thickness_mm
area_mm2
```

---

# Development Guidelines

When adding new project configuration:

1. Keep generic behavior in `framework`, not in project configuration.
2. Keep eWoodX-specific values under `projects.ewoodx.config`.
3. Place configuration in the module representing its responsibility.
4. Reuse existing shared values instead of duplicating them.
5. Re-export intended public configuration through `config/__init__.py`.
6. Keep units explicit in names where ambiguity is possible.
7. Document temporary compatibility configuration clearly.
8. Update this README when a new configuration group becomes part of the established project architecture.

Avoid moving hardware-specific values into the generic sensing framework simply because a framework class consumes them.

Likewise, avoid moving project-specific network identities, workspace domains, or Timber metadata into generic framework packages.

---

# Ongoing Development

This configuration package describes the **current eWoodX implementation**.

It is expected to evolve as the project gains:

```text
additional sensing equipment
additional agents
design workflows
robot-control workflows
new entity properties
new distributed services
new calibration requirements
new physical setups
```

Not every currently defined project area has the same implementation maturity.

Configuration should therefore follow actual project development rather than attempting to predict the complete final system in advance.

---

# Summary

`projects.ewoodx.config` is the central project-specific configuration layer.

```text
                    eWoodX CONFIG
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        ▼                ▼                ▼
    Workspace         Sensing          Entity
        │                │                │
        └────────┐       │       ┌────────┘
                 │       │       │
                 ▼       ▼       ▼
             Communication   Projection
```

It connects reusable framework capabilities to the current eWoodX deployment without embedding eWoodX-specific assumptions into the generic framework.

The central boundary is:

```text
FRAMEWORK
    │
    └── defines reusable capabilities

EWOODX CONFIG
    │
    └── defines how eWoodX currently configures them

EWOODX OPERATIONS / AGENTS / ENTRYPOINTS
    │
    └── use those configured capabilities
```

The package should continue evolving alongside the project while preserving that separation.