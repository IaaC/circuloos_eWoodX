# Camera Framework

The `framework.sensing.cameras` package groups reusable, equipment-specific camera acquisition, calibration, and image-space sensing capabilities.

The package currently provides implementations for:

```text
cameras/
├── arducam/
└── webcam_angetube/
```

These implementations follow a similar high-level organization:

```text
camera acquisition
        │
        ▼
intrinsic calibration
        │
        ▼
image-space detection
        │
        ▼
planar extrinsic calibration
```

However, they are deliberately **equipment-specific implementations rather than interchangeable implementations of one universal camera interface**.

The camera framework is under ongoing development. Additional camera and sensing-equipment packages are expected to be introduced as new hardware is integrated.

---

# Purpose

The camera package provides a common location for camera-related sensing capabilities while allowing each physical device to retain the configuration and processing behavior required by that equipment.

Conceptually:

```text
framework.sensing.cameras
          │
          ├── equipment A
          │      ├── acquisition
          │      ├── calibration
          │      └── detection
          │
          ├── equipment B
          │      ├── acquisition
          │      ├── calibration
          │      └── detection
          │
          └── future equipment
                 ├── device-specific acquisition
                 ├── device-specific calibration
                 └── device-specific capabilities
```

The package therefore provides organizational consistency without requiring all hardware to expose identical capabilities.

---

# Current Development Status

The camera framework is an **ongoing and extensible part of the sensing framework**.

The currently implemented packages are:

```text
arducam
webcam_angetube
```

They represent the camera equipment currently integrated into the framework.

They should not be interpreted as:

- a complete list of supported sensing hardware;
- a fixed camera architecture;
- a requirement that future equipment follow exactly the same internal implementation;
- a universal camera abstraction;
- a guarantee that every camera exposes identical configuration or calibration capabilities.

Future development may introduce additional equipment-specific packages as new cameras or sensing devices are integrated.

Conceptually:

```text
cameras/
│
├── arducam/
│
├── webcam_angetube/
│
├── <future_camera_01>/
│
├── <future_camera_02>/
│
└── ...
```

A future package may provide capabilities that do not exist in the current implementations, or may omit capabilities that are not relevant to that equipment.

The parent package should therefore evolve around actual shared requirements rather than forcing new hardware into an abstraction designed only around the currently available devices.

---

# Package Structure

The current structure is:

```text
framework/
└── sensing/
    └── cameras/
        ├── __init__.py
        │
        ├── arducam/
        │   ├── __init__.py
        │   ├── camera.py
        │   ├── intrinsic_calibration.py
        │   ├── extrinsic_calibration.py
        │   ├── aruco_detector.py
        │   └── README.md
        │
        └── webcam_angetube/
            ├── __init__.py
            ├── camera.py
            ├── intrinsic_calibration.py
            ├── extrinsic_calibration.py
            ├── aruco_detector.py
            └── README.md
```

Detailed device-specific behavior is documented in:

- [`arducam/README.md`](./arducam/README.md)
- [`webcam_angetube/README.md`](./webcam_angetube/README.md)

This parent README describes the camera layer as a whole rather than duplicating the detailed API documentation maintained by each equipment package.

---

# Current Public API

The package currently re-exports the public APIs of the two implemented camera packages.

```python
from framework.sensing.cameras import (
    ArducamCamera,
    ArducamIntrinsicCalibration,
    ArducamExtrinsicCalibration,
    ArducamArucoDetector,
    AngetubeCamera,
    AngetubeIntrinsicCalibration,
    AngetubeExtrinsicCalibration,
    AngetubeArucoDetector,
)
```

The current `__all__` contains:

```python
[
    "ArducamCamera",
    "ArducamIntrinsicCalibration",
    "ArducamExtrinsicCalibration",
    "ArducamArucoDetector",
    "AngetubeCamera",
    "AngetubeIntrinsicCalibration",
    "AngetubeExtrinsicCalibration",
    "AngetubeArucoDetector",
]
```

These exports provide convenient access to the currently implemented camera components.

---

# Public API Boundary

The parent package currently acts primarily as a **re-export boundary**.

Conceptually:

```text
framework.sensing.cameras
        │
        ├── Arducam public API
        │
        └── Angetube public API
```

It does not currently define objects such as:

```text
BaseCamera
CameraInterface
CameraManager
CalibrationManager
CameraFactory
EquipmentRegistry
```

and no such abstraction should be assumed from the package structure.

The current public API is the collection of explicitly exported equipment-specific classes.

---

# Equipment-Specific Design

Different camera hardware can require substantially different acquisition and calibration behavior.

The framework therefore keeps hardware-specific behavior inside equipment packages.

For example:

```text
Arducam
    │
    ├── OpenCV acquisition
    ├── resolution configuration
    ├── standard intrinsic calibration
    ├── ArUco detection
    └── planar homography calibration
```

while:

```text
Angetube
    │
    ├── OpenCV acquisition
    ├── resolution / FPS / FOURCC configuration
    ├── focus / exposure / image-property control
    ├── optional duvc_ctl hardware control
    ├── digital zoom
    ├── standard or fisheye intrinsic calibration
    ├── resolution-aware undistortion
    ├── ArUco detection
    └── planar homography calibration
```

The difference is intentional.

The framework does not currently attempt to hide these differences behind a lowest-common-denominator interface.

---

# Shared Conceptual Pattern

Although the implementations differ, the current camera packages share a useful conceptual decomposition.

```text
PHYSICAL CAMERA
       │
       ▼
ACQUISITION
       │
       ▼
IMAGE
       │
       ▼
INTRINSIC CALIBRATION
       │
       ▼
CALIBRATED IMAGE GEOMETRY
       │
       ▼
IMAGE-SPACE DETECTION
       │
       ▼
PIXEL INFORMATION
       │
       ▼
PHYSICAL CORRESPONDENCE
supplied by higher-level logic
       │
       ▼
PLANAR EXTRINSIC CALIBRATION
       │
       ▼
PHYSICAL PLANAR COORDINATES
```

This pattern currently appears in both implemented camera packages.

It is a useful organizational model, but it should not be interpreted as a mandatory interface that every future sensing device must implement.

---

# Acquisition Layer

The acquisition classes currently provide the interface between physical camera hardware and the rest of the sensing stack.

Current implementations are:

```python
ArducamCamera
AngetubeCamera
```

Both provide the basic lifecycle:

```text
configure
    │
    ▼
open
    │
    ▼
capture
    │
    ▼
close
```

However, their detailed configuration capabilities differ.

---

# Current Acquisition Comparison

| Capability | Arducam | Angetube |
|---|---:|---:|
| OpenCV acquisition | Yes | Yes |
| Camera index | Yes | Yes |
| Width / height request | Yes | Yes |
| Actual resolution query | Yes | Yes |
| Configurable OpenCV backend | Yes | Yes |
| FPS configuration | — | Yes |
| FOURCC configuration | — | Yes |
| Focus control | — | Yes |
| Exposure control | — | Yes |
| Brightness / contrast / saturation | — | Yes |
| Sharpness / gain / backlight control | — | Yes |
| White-balance control | — | Yes |
| Optional `duvc_ctl` control | — | Yes |
| Warm-up frames | — | Yes |
| Digital center zoom | — | Yes |

A missing capability in this table does not imply that the physical device can never support it.

It means that the capability is not part of the current framework implementation for that equipment package.

---

# Intrinsic Calibration Layer

The intrinsic calibration classes currently are:

```python
ArducamIntrinsicCalibration
AngetubeIntrinsicCalibration
```

Both use checkerboard observations to estimate camera intrinsics.

Conceptually:

```text
checkerboard images
       │
       ▼
corner detection
       │
       ▼
camera calibration
       │
       ├── camera matrix
       ├── distortion coefficients
       └── reprojection error
```

Both support:

- checkerboard configuration;
- physical square size in millimetres;
- calibration image processing;
- calibration result persistence;
- human-readable reports;
- loading saved calibration;
- image undistortion.

Their actual calibration models differ.

---

# Current Intrinsic Calibration Comparison

| Capability | Arducam | Angetube |
|---|---:|---:|
| Checkerboard calibration | Yes | Yes |
| Standard pinhole model | Yes | Yes |
| OpenCV fisheye model | — | Yes |
| Calibration persistence | Yes | Yes |
| Text calibration report | Yes | Yes |
| Undistortion | Yes | Yes |
| Resolution-aware intrinsic scaling | — | Yes |
| Cached undistortion maps | — | Yes |
| Configurable fisheye balance | — | Yes |
| Configurable fisheye FOV scale | — | Yes |

These differences remain documented in the equipment-specific READMEs rather than being hidden at this package level.

---

# Image-Space Detection

The currently implemented camera packages both provide ArUco detection:

```python
ArducamArucoDetector
AngetubeArucoDetector
```

The current detector responsibility is:

```text
image
   │
   ▼
detect marker
   │
   ▼
marker ID
   +
pixel corners
```

The detector does not define the physical meaning of those markers.

That distinction is important:

```text
marker detection
        ≠
physical marker interpretation
```

The camera layer can identify:

```text
marker ID 10
pixel corners [...]
```

while higher-level application logic decides whether that marker represents:

```text
workspace corner
reference point
calibration target
object identifier
or another physical meaning
```

---

# Planar Extrinsic Calibration

The current packages provide:

```python
ArducamExtrinsicCalibration
AngetubeExtrinsicCalibration
```

Both currently implement a planar homography:

```text
image pixel coordinates
        │
        ▼
homography
        │
        ▼
physical planar coordinates
        (millimetres)
```

This should not be confused with a general 3D camera extrinsic transform.

The current classes do not calculate:

```text
camera 3D pose
SE(3) transformation
full rotation + translation
camera-to-world rigid transformation
```

Instead, they map:

```text
(x_pixel, y_pixel)
        ↓
(x_mm, y_mm)
```

on a calibrated physical plane.

---

# Physical Correspondence Boundary

A key architectural boundary in the camera framework is that equipment-level marker detection does not define application-level physical geometry.

Conceptually:

```text
CAMERA PACKAGE

image
  │
  ▼
marker detection
  │
  ▼
pixel coordinates
```

then:

```text
HIGHER-LEVEL LOGIC

marker / reference interpretation
  │
  ▼
physical correspondence
```

then:

```text
CAMERA CALIBRATION

pixel points
      +
physical points
      │
      ▼
planar homography
```

This separation allows camera and detection components to remain reusable across different physical setups.

---

# Equipment Packages Are Not Required to Be Identical

The existence of similarly named components in the current packages does not establish a requirement that every future package contain:

```text
Camera
IntrinsicCalibration
ExtrinsicCalibration
ArucoDetector
```

A future camera might require:

```text
hardware SDK integration
depth acquisition
synchronized RGB-D acquisition
trigger control
device calibration
hardware timestamping
different fiducial detection
3D calibration
point-cloud generation
```

Another sensing device might not produce conventional camera images at all.

Therefore:

```text
shared package location
        ≠
identical hardware interface
```

The framework should preserve meaningful shared concepts while allowing equipment-specific capabilities where required.

---

# Future Equipment Integration

New equipment should normally be introduced as its own package under the relevant sensing category.

For camera equipment, the intended organizational direction is:

```text
cameras/
├── arducam/
├── webcam_angetube/
├── <new_camera>/
│   ├── __init__.py
│   ├── equipment-specific implementation
│   └── README.md
└── ...
```

A new equipment package should:

1. keep hardware-specific dependencies inside its own package where practical;
2. expose its intended public API through its `__init__.py`;
3. define `__all__` for the supported public objects;
4. document those objects in an equipment-specific README;
5. separate hardware behavior from application-specific sensing semantics;
6. avoid introducing project-specific workspace, entity, communication, or orchestration logic into the generic equipment layer.

Once the equipment API is established, selected public objects may be re-exported from:

```python
framework.sensing.cameras
```

when appropriate.

---

# Ongoing Framework Evolution

As more equipment is integrated, genuinely repeated patterns may become clearer.

For example, future development may reveal stable shared concepts around:

```text
camera lifecycle
frame acquisition
calibration persistence
device capabilities
hardware configuration
synchronized sensing
```

If those patterns become sufficiently stable, common abstractions may later be introduced.

However, the current framework deliberately avoids creating such abstractions prematurely.

The development direction is therefore:

```text
integrate real equipment
        │
        ▼
establish tested behavior
        │
        ▼
compare implementations
        │
        ▼
identify genuinely shared contracts
        │
        ▼
abstract only where useful
```

rather than:

```text
design universal abstraction first
        │
        ▼
force all equipment into it
```

This is especially important for sensing hardware, where device capabilities and SDK requirements can vary significantly.

---

# Relationship to Higher-Level Sensing

The camera layer provides equipment-level sensing capabilities.

It does not define complete application sensing operations.

Conceptually:

```text
framework.sensing.cameras
        │
        ├── hardware acquisition
        ├── hardware configuration
        ├── calibration
        └── image-space detection
        │
        ▼
higher-level sensing
        │
        ├── application interpretation
        ├── segmentation
        ├── measurement
        ├── physical object semantics
        └── result generation
```

The camera layer should remain independent of:

```text
workspace names
entry names
entity schemas
application object types
distributed actions
agent identities
project-specific measurement workflows
```

---

# Relationship to Workspace

The camera package does not persist workspace entities.

For example:

```text
camera.capture()
       │
       ▼
image
```

does not itself imply:

```text
create workspace
create entry
create entity
save application artifact
```

Those persistence decisions belong to higher-level sensing/application logic using the workspace framework.

This keeps:

```text
hardware acquisition
        ≠
application persistence
```

---

# Relationship to Communication

The camera package does not know whether its functionality is being executed:

```text
locally
from a command-line entrypoint
inside an agent
through a distributed workflow
or from another application
```

It does not depend on:

```text
Action
Agent
WorkflowClient
AgentPoller
TCPServer
```

Those concerns belong to the communication framework.

This allows the same equipment implementation to be used independently of distributed execution.

---

# Relationship to Orchestration

The camera package also does not determine:

```text
when sensing should begin
which workflow step is active
which action follows sensing
whether sensing belongs to a larger orchestration
```

Those decisions belong to orchestration and application-level logic.

The boundary is:

```text
ORCHESTRATION
     │
     ▼
decides that sensing should happen
     │
     ▼
APPLICATION / OPERATION
     │
     ▼
uses camera framework
     │
     ▼
physical acquisition
```

---

# Typical Usage

Applications may import directly from a specific equipment package:

```python
from framework.sensing.cameras.arducam import (
    ArducamCamera,
)
```

or:

```python
from framework.sensing.cameras.webcam_angetube import (
    AngetubeCamera,
)
```

The parent package also currently re-exports these objects:

```python
from framework.sensing.cameras import (
    ArducamCamera,
    AngetubeCamera,
)
```

Direct equipment-package imports make the hardware dependency explicit.

Parent-package imports provide a convenient consolidated public entry point.

---

# Choosing an Equipment Implementation

The parent package does not automatically select equipment.

There is currently no generic call such as:

```python
camera = create_camera(...)
```

or:

```python
camera = CameraFactory.create(...)
```

Instead, the caller explicitly selects the implementation it needs:

```python
camera = ArducamCamera(...)
```

or:

```python
camera = AngetubeCamera(...)
```

This keeps equipment choice visible and avoids hiding hardware-specific configuration behind an abstraction that does not yet represent all devices accurately.

---

# Current Public Objects

| Public object | Equipment | Responsibility |
|---|---|---|
| `ArducamCamera` | Arducam | Camera acquisition and basic resolution configuration. |
| `ArducamIntrinsicCalibration` | Arducam | Standard pinhole intrinsic calibration and undistortion. |
| `ArducamExtrinsicCalibration` | Arducam | Planar pixel-to-physical homography calibration. |
| `ArducamArucoDetector` | Arducam | ArUco marker detection in image coordinates. |
| `AngetubeCamera` | Angetube | Webcam acquisition, stream/property control, optional hardware control, and digital zoom. |
| `AngetubeIntrinsicCalibration` | Angetube | Standard or fisheye intrinsic calibration and resolution-aware undistortion. |
| `AngetubeExtrinsicCalibration` | Angetube | Planar pixel-to-physical homography calibration. |
| `AngetubeArucoDetector` | Angetube | ArUco marker detection in image coordinates. |

For complete constructor arguments, public attributes, methods, validation rules, persistence behavior, and examples, refer to the equipment-specific documentation:

- [`Arducam Camera Framework`](./arducam/README.md)
- [`Angetube Webcam Framework`](./webcam_angetube/README.md)

---

# Design Principles

The current camera framework follows several principles.

## 1. Equipment behavior remains equipment-specific

```text
shared sensing framework
        ≠
forced identical hardware implementation
```

---

## 2. Hardware acquisition remains separate from application semantics

```text
capture image
        ≠
interpret physical object
```

---

## 3. Detection remains separate from physical correspondence

```text
detect marker
        ≠
define marker meaning
```

---

## 4. Calibration remains separate from persistence

```text
compute calibration
        ≠
create application entity
```

---

## 5. Equipment remains separate from distributed execution

```text
camera operation
        ≠
communication lifecycle
```

---

## 6. Shared abstractions should emerge from tested common behavior

```text
multiple working implementations
        ↓
identify stable common requirements
        ↓
introduce abstraction if useful
```

rather than defining a universal hardware interface prematurely.

---

# Extending the Camera Framework

When integrating a new camera, a useful development sequence is:

```text
physical equipment
       │
       ▼
equipment-specific package
       │
       ▼
tested acquisition
       │
       ▼
required calibration / processing
       │
       ▼
equipment public API
       │
       ▼
equipment README
       │
       ▼
optional parent-package re-export
```

The exact internal files do not need to match the existing Arducam or Angetube packages if the new equipment requires a different architecture.

The important boundary is that the package should expose reusable equipment capabilities without embedding application-specific workflow semantics.

---

# Summary

The `framework.sensing.cameras` package is the equipment-specific camera layer of the sensing framework.

Currently:

```text
framework.sensing.cameras
        │
        ├── arducam
        │     ├── acquisition
        │     ├── intrinsic calibration
        │     ├── ArUco detection
        │     └── planar extrinsic calibration
        │
        └── webcam_angetube
              ├── acquisition
              ├── extended camera control
              ├── standard / fisheye calibration
              ├── ArUco detection
              └── planar extrinsic calibration
```

The package is under ongoing development.

Future camera and sensing-equipment integrations are expected to extend this structure as required by their hardware capabilities.

The central architectural principle is:

```text
COMMON ORGANIZATION
        +
EQUIPMENT-SPECIFIC IMPLEMENTATION
        +
APPLICATION-INDEPENDENT CAPABILITIES
```

rather than:

```text
ONE FIXED INTERFACE
FOR EVERY SENSING DEVICE
```

This allows the sensing framework to grow with new equipment while preserving clear boundaries between hardware access, calibration, physical interpretation, application persistence, communication, and orchestration.