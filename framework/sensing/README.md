# Sensing Framework

The `framework.sensing` package provides reusable equipment-level capabilities for acquiring and calibrating physical sensing data.

The sensing framework is designed as an **extensible and ongoing part of the framework**. Its purpose is to provide reusable interfaces to physical sensing equipment without embedding application-specific object semantics, persistence workflows, communication protocols, or orchestration logic into the hardware layer.

The currently implemented sensing category is:

```text
sensing/
└── cameras/
```

with camera-specific implementations for:

```text
cameras/
├── arducam/
└── webcam_angetube/
```

Future development is expected to introduce additional sensing equipment and sensing categories as required.

The current structure should therefore be understood as the **present implementation state**, not as a complete definition of what the sensing framework may contain.

---

# Purpose

The sensing framework provides the boundary between physical sensing equipment and higher-level application logic.

Conceptually:

```text
PHYSICAL ENVIRONMENT
        │
        ▼
SENSING EQUIPMENT
        │
        ▼
framework.sensing
        │
        ├── acquisition
        ├── equipment configuration
        ├── calibration
        └── equipment-level processing
        │
        ▼
SENSING DATA
        │
        ▼
HIGHER-LEVEL APPLICATION
        │
        ├── interpretation
        ├── measurement
        ├── object semantics
        ├── persistence
        └── workflow decisions
```

The sensing framework therefore answers questions such as:

```text
How is data acquired from this device?

How is the equipment configured?

How is its geometry calibrated?

What reusable equipment-level processing
is required before application interpretation?
```

It deliberately does not answer:

```text
What application object is being sensed?

How should that object be identified?

Where should its results be stored?

Which distributed agent should execute sensing?

Which workflow step should follow sensing?
```

Those concerns belong to other framework or application layers.

---

# Current Development Status

The sensing framework is under **ongoing development**.

At present, the implemented hierarchy is:

```text
framework/
└── sensing/
    ├── __init__.py
    │
    └── cameras/
        ├── __init__.py
        ├── README.md
        │
        ├── arducam/
        │   ├── camera.py
        │   ├── intrinsic_calibration.py
        │   ├── extrinsic_calibration.py
        │   ├── aruco_detector.py
        │   └── README.md
        │
        └── webcam_angetube/
            ├── camera.py
            ├── intrinsic_calibration.py
            ├── extrinsic_calibration.py
            ├── aruco_detector.py
            └── README.md
```

The only currently implemented sensing category is:

```text
cameras
```

This does **not** mean that the sensing framework is intended only for cameras.

As development continues, other sensing categories may be added when their equipment is integrated and their actual requirements are established.

Possible future categories could include equipment such as:

```text
depth / RGB-D sensing
LiDAR
3D scanners
thermal sensing
distance sensors
tracking systems
other spatial sensing equipment
```

These are architectural extension possibilities, not claims that such implementations currently exist in the package.

---

# Extensible Sensing Structure

The intended direction is that different families of sensing equipment can occupy their own categories.

Conceptually:

```text
framework.sensing
        │
        ├── cameras/
        │      ├── equipment implementation
        │      └── equipment implementation
        │
        ├── <future sensing category>/
        │      ├── equipment implementation
        │      └── equipment implementation
        │
        └── ...
```

For example, the structure may eventually evolve toward something conceptually similar to:

```text
sensing/
├── cameras/
│   ├── camera_a/
│   └── camera_b/
│
├── <future_category_a>/
│   └── ...
│
├── <future_category_b>/
│   └── ...
│
└── ...
```

The exact categories should emerge from real equipment integrations rather than being fixed in advance.

---

# Sensing Architecture

The sensing framework follows a layered equipment organization:

```text
SENSING
   │
   ▼
EQUIPMENT CATEGORY
   │
   ▼
EQUIPMENT-SPECIFIC PACKAGE
   │
   ▼
DEVICE CAPABILITIES
```

Using the current implementation:

```text
framework.sensing
       │
       ▼
cameras
       │
       ├── arducam
       │      │
       │      ├── acquisition
       │      ├── intrinsic calibration
       │      ├── ArUco detection
       │      └── planar calibration
       │
       └── webcam_angetube
              │
              ├── acquisition
              ├── camera control
              ├── intrinsic calibration
              ├── ArUco detection
              └── planar calibration
```

This provides organization without requiring every sensing device to expose the same capabilities.

---

# Equipment-Specific Design

Physical sensing hardware can vary substantially.

Different devices may require:

```text
different SDKs
different drivers
different calibration models
different data formats
different synchronization mechanisms
different acquisition lifecycles
different hardware controls
different coordinate systems
different processing pipelines
```

The framework therefore keeps equipment-specific behavior close to the equipment implementation.

For example, the two current cameras already demonstrate this principle:

```text
Arducam
   │
   └── relatively simple OpenCV acquisition
       + standard calibration
```

versus:

```text
Angetube
   │
   └── OpenCV acquisition
       + hardware/property control
       + optional duvc_ctl
       + digital zoom
       + standard/fisheye calibration
```

The sensing framework does not force these devices into identical implementations merely because both are cameras.

The same principle should apply even more strongly when integrating fundamentally different sensing technologies.

---

# No Universal Sensor Interface

The package does not currently define a universal abstraction such as:

```text
Sensor
BaseSensor
SensorInterface
SensorManager
EquipmentManager
SensorFactory
SensorRegistry
```

No such interface should be assumed from the package hierarchy.

The current development strategy is:

```text
integrate equipment
       │
       ▼
establish working behavior
       │
       ▼
identify repeated patterns
       │
       ▼
introduce shared abstraction
only when justified
```

rather than:

```text
define universal sensor abstraction
       │
       ▼
force every device to implement it
```

This prevents the framework from being constrained by assumptions derived from only the first few pieces of hardware.

---

# Current Public API

The current `framework.sensing` package re-exports the public camera APIs.

```python
from framework.sensing import (
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

The current `__all__` is:

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

At present:

```text
framework.sensing
       │
       ▼
re-exports
       │
       ▼
framework.sensing.cameras
       │
       ▼
equipment-specific camera APIs
```

The parent sensing package does not currently add another behavioral abstraction above these classes.

---

# Current Public Objects

| Public object | Category | Equipment | Responsibility |
|---|---|---|---|
| `ArducamCamera` | Camera | Arducam | Camera acquisition and basic resolution configuration. |
| `ArducamIntrinsicCalibration` | Camera | Arducam | Standard intrinsic calibration and undistortion. |
| `ArducamExtrinsicCalibration` | Camera | Arducam | Planar pixel-to-physical homography calibration. |
| `ArducamArucoDetector` | Camera | Arducam | ArUco detection in image coordinates. |
| `AngetubeCamera` | Camera | Angetube | Webcam acquisition, stream/property control, optional hardware control, and digital zoom. |
| `AngetubeIntrinsicCalibration` | Camera | Angetube | Standard or fisheye intrinsic calibration and undistortion. |
| `AngetubeExtrinsicCalibration` | Camera | Angetube | Planar pixel-to-physical homography calibration. |
| `AngetubeArucoDetector` | Camera | Angetube | ArUco detection in image coordinates. |

Detailed behavior belongs in the lower-level documentation:

- [`Camera Framework`](./cameras/README.md)
- [`Arducam Camera Framework`](./cameras/arducam/README.md)
- [`Angetube Webcam Framework`](./cameras/webcam_angetube/README.md)

---

# Sensing Responsibility Boundary

The sensing framework owns reusable equipment-level capabilities.

A useful boundary is:

```text
SENSING FRAMEWORK
        │
        ├── connect to equipment
        ├── configure equipment
        ├── acquire sensor data
        ├── calibrate equipment
        └── perform reusable
            equipment-level processing
```

while:

```text
APPLICATION
        │
        ├── decide what is being sensed
        ├── interpret sensor output
        ├── derive application measurements
        ├── assign object identity
        ├── persist application artifacts
        └── determine workflow meaning
```

This distinction allows equipment implementations to be reused by multiple applications.

---

# Equipment Data vs Application Information

The sensing framework primarily produces equipment-level data.

For example, a camera may produce:

```text
image
marker ID
pixel coordinate
calibration matrix
distortion coefficients
```

A future scanner might produce:

```text
point cloud
depth data
device pose
scan metadata
```

A future thermal device might produce:

```text
temperature image
temperature samples
sensor metadata
```

Higher-level application logic may interpret those data as:

```text
object boundary
material dimension
defect
physical component
inspection result
application entity
```

The distinction is:

```text
sensor observation
        ≠
application meaning
```

---

# Calibration Boundary

Calibration belongs in the sensing layer when it describes the relationship between the sensing equipment and the data it produces.

Current examples include:

```text
camera intrinsic calibration
        │
        └── camera image geometry

planar homography calibration
        │
        └── image pixels → physical plane
```

Future equipment may require different calibration mechanisms.

For example:

```text
sensor-to-sensor calibration
sensor-to-tool calibration
depth calibration
3D extrinsic calibration
time synchronization calibration
```

Such capabilities should be introduced according to actual equipment requirements.

The existence of the current camera calibration classes does not imply that all future sensing equipment must use the same calibration model.

---

# Acquisition Boundary

Equipment acquisition belongs in the sensing layer.

Conceptually:

```text
physical sensor
      │
      ▼
equipment driver / SDK / API
      │
      ▼
framework.sensing
      │
      ▼
sensor data
```

The sensing framework may therefore contain dependencies specific to a piece of hardware or its SDK within the appropriate equipment package.

Higher-level application logic should not need to reproduce low-level equipment communication merely to obtain sensor data.

---

# Processing Boundary

Some processing belongs naturally close to the sensing equipment.

Current examples include:

```text
image undistortion
ArUco detection
digital image zoom
```

These operations directly concern the geometry or behavior of the sensor data.

By contrast, application-specific processing such as:

```text
material segmentation
object classification
application measurement
domain-specific defect interpretation
```

should generally remain outside the generic sensing equipment package unless it becomes a genuinely reusable sensing capability.

A useful distinction is:

```text
Does this operation describe
the sensor/data itself?
        │
       YES
        │
        ▼
candidate for sensing framework
```

versus:

```text
Does this operation describe
what the application believes
the sensed object means?
        │
       YES
        │
        ▼
application-level logic
```

---

# Relationship to Application Operations

The sensing framework provides capabilities that higher-level operations can compose.

Conceptually:

```text
APPLICATION OPERATION
        │
        ├── choose equipment
        │
        ▼
framework.sensing
        │
        ├── acquire
        ├── calibrate
        └── preprocess
        │
        ▼
sensor result
        │
        ▼
APPLICATION OPERATION
        │
        ├── segment
        ├── measure
        ├── interpret
        └── persist
```

The sensing package itself should not become the owner of complete application workflows.

---

# Relationship to Workspace

The sensing framework does not own workspace organization or application persistence.

For example:

```text
sensor
   │
   ▼
capture data
```

does not automatically imply:

```text
Workspace
   │
   ▼
Domain
   │
   ▼
Entry
   │
   ▼
Entity
```

Those decisions belong to the workspace and application layers.

The separation is:

```text
framework.sensing
        │
        └── produces sensing data
```

and:

```text
framework.workspace
        │
        └── provides persistent
            organizational structures
```

A higher-level application can connect them when required.

---

# Relationship to Communication

The sensing framework does not own distributed execution.

A sensing component should be usable regardless of whether it is called:

```text
directly from Python
from a local application
from an entrypoint
inside an agent process
through a distributed action
```

The sensing equipment itself does not need to know:

```text
which agent requested the operation
which TCP connection initiated it
which Action is active
whether the caller is local or remote
```

Those concerns belong to:

```text
framework.communication
```

The architectural boundary is:

```text
COMMUNICATION
      │
      ▼
requests execution
      │
      ▼
APPLICATION / OPERATION
      │
      ▼
uses sensing framework
      │
      ▼
PHYSICAL SENSOR
```

---

# Relationship to Orchestration

The sensing framework does not determine when sensing should happen within a larger process.

It does not define:

```text
workflow order
step dependencies
action release
workflow progression
```

Those concerns belong to:

```text
framework.orchestration
```

Conceptually:

```text
ORCHESTRATION
      │
      ▼
release sensing action
      │
      ▼
COMMUNICATION / EXECUTION
      │
      ▼
application sensing operation
      │
      ▼
framework.sensing
      │
      ▼
physical equipment
```

The sensing package remains reusable independently of that execution path.

---

# Relationship to Communication Status

The sensing framework also does not own action lifecycle state.

For example, it does not determine:

```text
PENDING
CLAIMED
RUNNING
COMPLETED
FAILED
CANCELLED
```

A camera capture failure may raise an exception, but deciding that the corresponding distributed action becomes:

```text
FAILED
```

belongs to the execution/communication layer.

This preserves the broader framework principle that execution lifecycle ownership remains separate from equipment implementation.

---

# Current Camera Category

The current implemented sensing category is documented separately:

[`framework.sensing.cameras`](./cameras/README.md)

Its present structure is:

```text
cameras/
├── arducam/
└── webcam_angetube/
```

The camera parent package documents:

- current equipment implementations;
- current shared conceptual patterns;
- equipment differences;
- camera-level calibration;
- camera-level public API;
- future camera extension.

This sensing README intentionally does not duplicate those detailed camera APIs.

---

# Adding a New Device to an Existing Category

If a new piece of equipment belongs naturally to an existing category, it should normally be added as an equipment-specific package within that category.

For example:

```text
sensing/
└── cameras/
    ├── arducam/
    ├── webcam_angetube/
    └── <new_camera>/
```

The new package should establish:

```text
equipment-specific implementation
        │
        ▼
tested behavior
        │
        ▼
public API
        │
        ▼
equipment README
```

Selected public objects may then be re-exported through the parent category and sensing packages where appropriate.

---

# Adding a New Sensing Category

If equipment does not fit the responsibilities of an existing category, a new sensing category may be appropriate.

Conceptually:

```text
sensing/
├── cameras/
└── <new_category>/
```

A new category should represent a meaningful family of sensing capabilities rather than simply becoming another arbitrary directory.

The development process should be driven by actual implementation requirements.

A useful progression is:

```text
new physical equipment
       │
       ▼
identify equipment requirements
       │
       ▼
determine whether an existing
category represents them
       │
   ┌───┴────┐
  YES       NO
   │         │
   ▼         ▼
existing    establish new
category    sensing category
```

---

# Development Principles

The sensing framework follows several principles.

## 1. Integrate real equipment before generalizing

```text
working equipment implementation
        ↓
tested behavior
        ↓
shared pattern
        ↓
possible abstraction
```

---

## 2. Keep hardware-specific behavior close to the hardware

```text
device SDK
device properties
device calibration
        │
        ▼
equipment package
```

---

## 3. Keep application semantics outside generic equipment packages

```text
sensor observation
        ≠
application object
```

---

## 4. Do not require unrelated sensing technologies to expose identical APIs

```text
camera
LiDAR
scanner
thermal sensor
        │
        ▼
different capabilities are valid
```

---

## 5. Separate sensing from persistence

```text
acquire data
        ≠
store application entity
```

---

## 6. Separate sensing from communication

```text
use physical equipment
        ≠
manage distributed action
```

---

## 7. Separate sensing from orchestration

```text
perform sensing
        ≠
decide workflow progression
```

---

## 8. Let abstractions emerge from repeated tested behavior

The framework should avoid introducing generic sensor managers, registries, factories, or base classes until multiple real implementations demonstrate that such abstractions are useful.

---

# Public API Boundary

The intended public API of the sensing package is defined by:

```python
framework.sensing.__all__
```

At present, it consists entirely of the public objects re-exported from:

```text
framework.sensing.cameras
```

Future sensing categories may extend this public API.

When that occurs, this README should be updated to reflect the new implemented capabilities rather than documenting anticipated APIs before they exist.

---

# Documentation Hierarchy

Detailed documentation follows the same inside-to-outside structure as the code.

```text
Sensing Framework
README.md
    │
    ▼
Camera Framework
cameras/README.md
    │
    ├───────────────┐
    ▼               ▼
Arducam          Angetube
README.md        README.md
```

Use the lowest relevant documentation level when detailed implementation information is required.

### Camera framework

[`cameras/README.md`](./cameras/README.md)

Documents the camera category, current implementations, shared patterns, equipment differences, and camera extension strategy.

### Arducam

[`cameras/arducam/README.md`](./cameras/arducam/README.md)

Documents the complete public API and behavior of the current Arducam implementation.

### Angetube

[`cameras/webcam_angetube/README.md`](./cameras/webcam_angetube/README.md)

Documents the complete public API and behavior of the current Angetube webcam implementation.

---

# Summary

The `framework.sensing` package provides the generic organizational layer for reusable physical sensing capabilities.

Its current implementation is:

```text
framework.sensing
       │
       ▼
cameras
       │
       ├── arducam
       └── webcam_angetube
```

but its architectural scope is broader:

```text
framework.sensing
       │
       ├── current sensing category
       │
       ├── future sensing category
       │
       ├── future sensing category
       │
       └── ...
```

The framework is under ongoing development, and new sensing equipment should be incorporated according to its actual hardware and processing requirements.

The central boundary is:

```text
PHYSICAL EQUIPMENT
        │
        ▼
SENSING FRAMEWORK
        │
        ▼
REUSABLE SENSOR DATA / CAPABILITIES
        │
        ▼
APPLICATION INTERPRETATION
```

while:

```text
sensing
    ≠ application semantics
    ≠ persistence
    ≠ communication
    ≠ orchestration
```

The sensing framework therefore provides an extensible foundation for physical data acquisition without prematurely defining one universal model for all present and future sensing equipment.