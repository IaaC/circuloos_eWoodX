# eWoodX Operations

The `projects.ewoodx.operations` package contains the concrete operational logic used by the eWoodX application.

Operations are where reusable framework capabilities, project configuration, physical equipment, and eWoodX-specific semantics are composed into executable tasks.

The package currently includes operations for:

- project-specific Entry and entity ID allocation;
- camera calibration and equipment tuning;
- Timber sensing and measurement;
- persistent Timber entity creation;
- projector calibration;
- live projection and external geometry streaming.

The operations package is under **continuous development**. The current modules represent the operational workflows implemented and tested so far and should not be interpreted as the final set of eWoodX capabilities.

---

# Package Structure

The current operations are organized as:

```text
projects/ewoodx/operations/
├── __init__.py
│
├── entry_allocator.py
├── entity_id_allocator.py
│
├── calibrate_arducam_intrinsic.py
├── calibrate_arducam_extrinsic.py
├── calibrate_angetube_intrinsic.py
├── calibrate_angetube_extrinsic.py
├── tune_angetube_camera.py
│
├── timber_segmentation_arducam.py
├── timber_segmentation_angetube.py
│
├── calibrate_projector_auto.py
├── calibrate_projector_corners.py
│
└── projector_live_viewer.py
```

These modules can be grouped conceptually as:

```text
OPERATIONS
    │
    ├── Project Identity / Allocation
    │      ├── entry_allocator.py
    │      └── entity_id_allocator.py
    │
    ├── Camera Calibration / Setup
    │      ├── calibrate_arducam_intrinsic.py
    │      ├── calibrate_arducam_extrinsic.py
    │      ├── calibrate_angetube_intrinsic.py
    │      ├── calibrate_angetube_extrinsic.py
    │      └── tune_angetube_camera.py
    │
    ├── Timber Sensing
    │      ├── timber_segmentation_arducam.py
    │      └── timber_segmentation_angetube.py
    │
    └── Projection
           ├── calibrate_projector_auto.py
           ├── calibrate_projector_corners.py
           └── projector_live_viewer.py
```

---

# Architectural Role

The operations package is the main project-level composition layer between generic framework capabilities and concrete eWoodX tasks.

Conceptually:

```text
                 eWoodX OPERATION
                       │
        ┌──────────────┼──────────────┐
        │              │              │
        ▼              ▼              ▼
     CONFIG         FRAMEWORK      PROJECT DATA
        │              │              │
        │              ▼              │
        │       reusable capability   │
        │              │              │
        └──────────────┼──────────────┘
                       │
                       ▼
               operational behavior
                       │
                       ▼
             PHYSICAL / DIGITAL SYSTEM
```

For example, a Timber sensing operation combines:

```text
eWoodX camera configuration
          +
framework camera acquisition
          +
framework camera calibration
          +
eWoodX marker arrangement
          +
eWoodX Timber segmentation
          +
eWoodX measurement logic
          +
framework EntityManager
          +
eWoodX entity ID convention
```

into one executable sensing workflow.

This is the intended distinction between framework and project operations:

```text
framework
    │
    └── reusable mechanism

projects.ewoodx.operations
    │
    └── concrete eWoodX behavior
```

---

# Package Public API

The current:

```text
projects/ewoodx/operations/__init__.py
```

does not re-export operation classes.

Therefore, the package currently has **no consolidated package-level public API** through `operations.__all__`.

Operations are currently imported directly from their modules when required.

For example:

```python
from projects.ewoodx.operations.timber_segmentation_angetube import (
    EWoodXTimberSegmentationAngetube,
)
```

and:

```python
from projects.ewoodx.operations.entity_id_allocator import (
    EWoodXEntityIdAllocator,
)
```

This README documents the important operational classes and their intended responsibilities, but it does not imply that every class has been promoted to a stable package-level API.

---

# Current Operation Groups

The current package contains four main operational groups:

| Group | Responsibility |
|---|---|
| Project identity / allocation | Apply project-specific conventions for Entry allocation and persistent entity IDs. |
| Camera calibration / setup | Produce camera calibration data and support equipment-specific camera setup and tuning. |
| Timber sensing | Acquire, segment, measure, visualize, and persist sensed Timber. |
| Projection | Calibrate the projector and render geometry onto the physical workspace. |

These groups do not represent a fixed final architecture.

Additional operations are expected as the project develops.

---

# Project Identity and Allocation

The operations package currently contains two project-specific allocation mechanisms:

```text
EWoodXEntryAllocator
        │
        └── project Entry naming/allocation

EWoodXEntityIdAllocator
        │
        └── persistent entity ID allocation
```

The generic workspace framework owns the underlying Entry and Entity persistence mechanisms.

The eWoodX operations layer owns the project-specific conventions used to allocate their identities.

---

# Entry Allocation

Defined in:

```text
entry_allocator.py
```

Primary class:

```python
EWoodXEntryAllocator
```

The allocator provides the project-specific convention used when creating and identifying new eWoodX Entries.

It operates together with the generic:

```python
framework.workspace.EntryManager
```

Conceptually:

```text
EntryManager
    │
    └── generic Entry persistence and management

EWoodXEntryAllocator
    │
    └── eWoodX-specific Entry allocation convention
```

The current sensing entrypoint uses this allocator when creating new sensing Entries and when resolving the latest project-managed Entry.

This keeps project naming/allocation behavior outside the generic workspace framework.

---

# Entity ID Allocation

Defined in:

```text
entity_id_allocator.py
```

Primary class:

```python
EWoodXEntityIdAllocator
```

The allocator provides the project-specific naming convention for persistent entities.

The generic workspace framework owns:

```text
entity existence
entity persistence
entity lookup
entity indexing
```

while eWoodX owns:

```text
entity naming convention
persistent sequence
project prefix
random ID component
```

This separation is explicitly reflected in the implementation.

---

# `EWoodXEntityIdAllocator`

Constructor:

```python
EWoodXEntityIdAllocator(
    entity_manager: EntityManager,
)
```

The constructor requires an existing generic:

```python
framework.workspace.EntityManager
```

and validates that the supplied object is an `EntityManager`.

The allocator stores its persistent counter file under:

```text
<workspace>/
└── index/
    └── entity_counters.json
```

The current counter filename is:

```python
COUNTER_FILE = "entity_counters.json"
```

---

# Entity ID Format

The main public operation is:

```python
allocate(
    entity_type: str,
    prefix: str,
) -> str
```

A generated ID follows the pattern:

```text
PREFIX-SEQUENCE-RANDOM
```

For example:

```text
T-0001-K7M
```

The individual components are configured through `projects.ewoodx.config`.

Conceptually:

```text
T
│
└── project/entity prefix

0001
│
└── persistent sequence

K7M
│
└── random component
```

Before accepting a generated ID, the allocator checks:

```python
entity_manager.exists(candidate_id)
```

to prevent collision with an already registered entity.

---

# Persistent Entity Counters

Counters are maintained per entity type.

Conceptually:

```json
{
    "entity_counters": {
        "timber": 12
    }
}
```

The counter file is written through a temporary file and then replaced:

```text
entity_counters.json.tmp
        │
        ▼
entity_counters.json
```

This provides atomic replacement of the counter file.

The sequence is persistent at the workspace level rather than being reset each time an operation starts.

---

# Camera Calibration Operations

The project currently contains calibration workflows for two cameras:

```text
Arducam
Angetube Webcam
```

Each currently has:

```text
intrinsic calibration
        +
planar extrinsic calibration
```

The project operations wrap reusable classes from:

```text
framework.sensing
```

with eWoodX-specific:

```text
camera configuration
calibration directories
checkerboard configuration
ArUco arrangement
physical coordinates
interactive workflow
```

The Angetube camera additionally has a project-level tuning utility for configuring acquisition behavior during equipment setup.

---

# Calibration Architecture

The general relationship is:

```text
projects.ewoodx.config
        │
        │ physical/project setup
        ▼
eWoodX Calibration Operation
        │
        │ composes
        ▼
framework.sensing
        │
        ├── Camera
        ├── IntrinsicCalibration
        ├── ArucoDetector
        └── ExtrinsicCalibration
        │
        ▼
calibration artifacts
```

The mathematical camera capabilities remain reusable framework functionality.

The interactive calibration procedure and physical eWoodX setup remain project operations.

---

# Arducam Intrinsic Calibration

Defined in:

```text
calibrate_arducam_intrinsic.py
```

Primary class:

```python
EWoodXArducamIntrinsicCalibration
```

Constructor:

```python
EWoodXArducamIntrinsicCalibration(
    calibration_images_directory: Path | None = None,
    output_file: Path | None = None,
)
```

If paths are not supplied, the operation uses the configured eWoodX calibration structure.

The operation composes:

```python
ArducamCamera
```

and:

```python
ArducamIntrinsicCalibration
```

from the generic sensing framework.

---

# Arducam Intrinsic Workflow

The primary operational methods are:

```python
capture_images()
calibrate()
run()
```

Conceptually:

```text
open camera
    │
    ▼
show live checkerboard view
    │
    ▼
capture calibration images
    │
    ▼
find stored calibration images
    │
    ▼
framework intrinsic calibration
    │
    ▼
save calibration
```

During interactive capture:

```text
SPACE → capture image
ENTER → finish capture
```

The operation displays whether the checkerboard is currently detected but allows an image to be saved even when complete checkerboard detection is not available.

The framework calibration stage subsequently determines which stored images can actually contribute to calibration.

---

# Arducam Intrinsic Output

The default calibration location is based on:

```text
calibration_data/
└── arducam/
    └── intrinsic/
        ├── images/
        └── camera_intrinsics.npz
```

The exact project paths are defined in `projects.ewoodx.config`.

The reusable framework calibration class owns the calibration mathematics and calibration-file representation.

---

# Arducam Extrinsic Calibration

Defined in:

```text
calibrate_arducam_extrinsic.py
```

Primary class:

```python
EWoodXArducamExtrinsicCalibration
```

Constructor:

```python
EWoodXArducamExtrinsicCalibration(
    intrinsic_file: Path | None = None,
    calibration_image: Path | None = None,
    output_file: Path | None = None,
)
```

The operation composes:

```python
ArducamCamera
ArducamArucoDetector
ArducamExtrinsicCalibration
ArducamIntrinsicCalibration
```

with the physical marker arrangement defined by the eWoodX configuration.

---

# Arducam Extrinsic Workflow

The main methods are:

```python
capture_image()
calibrate()
run()
```

The workflow is:

```text
load intrinsic calibration
        │
        ▼
capture reference workspace
        │
        ▼
undistort image
        │
        ▼
detect configured ArUco markers
        │
        ▼
construct pixel ↔ physical correspondences
        │
        ▼
calculate planar homography
        │
        ▼
save calibration
```

Interactive capture uses:

```text
SPACE → capture and continue
ENTER → exit without calibration
```

The physical marker coordinates are supplied by:

```text
projects.ewoodx.config
```

rather than being defined by the generic ArUco detector.

---

# Angetube Intrinsic Calibration

Defined in:

```text
calibrate_angetube_intrinsic.py
```

Primary class:

```python
EWoodXAngetubeIntrinsicCalibration
```

The operation provides the same project-level responsibility as the Arducam intrinsic workflow, but uses the Angetube-specific sensing framework implementation and camera configuration.

The operation composes:

```python
AngetubeCamera
AngetubeIntrinsicCalibration
```

with the current eWoodX Angetube configuration.

The primary workflow methods are:

```python
capture_images()
calibrate()
run()
```

The operation handles the interactive capture workflow while the generic framework class performs the intrinsic calibration.

The current Angetube configuration supports the calibration model selected in:

```text
projects.ewoodx.config
```

which is currently configured for fisheye calibration.

---

# Angetube Extrinsic Calibration

Defined in:

```text
calibrate_angetube_extrinsic.py
```

Primary class:

```python
EWoodXAngetubeExtrinsicCalibration
```

The operation composes:

```python
AngetubeCamera
AngetubeArucoDetector
AngetubeExtrinsicCalibration
AngetubeIntrinsicCalibration
```

with the current eWoodX physical marker arrangement.

The primary methods are:

```python
capture_image()
calibrate()
run()
```

The conceptual workflow is:

```text
camera
   │
   ▼
capture reference image
   │
   ▼
intrinsic undistortion
   │
   ▼
ArUco detection
   │
   ▼
eWoodX physical marker interpretation
   │
   ▼
planar homography
   │
   ▼
calibration artifact
```

---

# Angetube Camera Tuning

Defined in:

```text
tune_angetube_camera.py
```

This operation provides an equipment-specific utility for interactively tuning the current Angetube webcam configuration.

Its purpose is different from camera calibration:

```text
CAMERA CALIBRATION
       │
       └── determines the geometric camera model

CAMERA TUNING
       │
       └── adjusts camera/device parameters for acquisition
```

The tuning operation therefore belongs to the project operational layer because it supports preparation of the specific camera used by the current eWoodX sensing setup.

It should not be interpreted as part of the generic camera calibration mathematics provided by `framework.sensing`.

Conceptually:

```text
Angetube Camera
       │
       ▼
Camera Tuning
       │
       ▼
configured acquisition behavior
       │
       ▼
Calibration / Sensing Operations
```

The utility supports development and physical setup of the current Angetube sensing workflow.

---

# Timber Sensing Operations

The current project contains two camera-specific Timber sensing operations:

```text
timber_segmentation_arducam.py
timber_segmentation_angetube.py
```

with primary classes:

```python
EWoodXTimberSegmentationArducam
EWoodXTimberSegmentationAngetube
```

Both implement the same overall eWoodX sensing workflow using different camera implementations.

They are application operations rather than generic sensing framework components because they contain Timber-specific:

```text
segmentation
measurement
geometry
color extraction
entity creation
artifact persistence
```

---

# Timber Sensing Architecture

The current sensing operation can be understood as:

```text
Camera
  │
  ▼
Capture
  │
  ▼
Intrinsic Undistortion
  │
  ▼
ArUco Detection
  │
  ▼
Live Planar Homography
  │
  ▼
Workspace Detection
  │
  ▼
Timber Segmentation
  │
  ▼
Geometry + Color
  │
  ▼
Measurement
  │
  ▼
Persistent Timber Entity
```

The lower-level camera and calibration capabilities come from:

```text
framework.sensing
```

while persistent entity management comes from:

```text
framework.workspace
```

The Timber interpretation connecting those capabilities belongs to:

```text
projects.ewoodx.operations
```

---

# Live Sensing

Both current Timber sensing classes expose:

```python
run() -> None
```

for the interactive sensing loop.

During operation they continuously:

```text
capture frame
     │
     ▼
undistort
     │
     ▼
detect reference markers
     │
     ▼
calculate current homography
     │
     ▼
segment Timber
     │
     ▼
calculate measurement
     │
     ▼
render live preview
```

The current terminal commands are:

```text
S = save current valid Timber
T = change Timber thickness
Q = quit
```

---

# Per-Frame Processing

Both sensing operations expose:

```python
process_frame(
    frame: np.ndarray,
) -> dict
```

The returned dictionary represents either a valid or invalid current sensing result.

A valid result contains the current:

```text
frame
undistorted frame
preview
mask
measurement
```

and reports:

```python
"valid": True
```

If the required reference markers are not visible or no valid Timber can be segmented, the result reports:

```python
"valid": False
```

with the corresponding preview and available intermediate data.

This allows the live sensing loop to continue even when an individual frame cannot produce a valid measurement.

---

# Live Homography

A notable part of the current Timber sensing workflow is that the planar homography is recalculated from the reference markers for the current frame.

Conceptually:

```text
current frame
     │
     ▼
reference markers
     │
     ▼
current pixel coordinates
     │
     +
configured physical coordinates
     │
     ▼
fresh homography
```

This allows the sensing operation to derive the current relationship between image coordinates and the physical reference workspace.

The generic homography calculation is provided by the framework.

The marker arrangement and physical workspace interpretation are project-specific.

---

# Timber Geometry

After segmentation, detected Timber geometry is transformed from image coordinates into physical coordinates.

The operation derives project-level measurement information including geometry such as:

```text
Timber corners
Timber contour
length
width
area
thickness
```

with physical geometry represented in millimetres and area in square millimetres where applicable.

The exact measurement logic belongs to the eWoodX operation rather than to the generic camera package.

---

# Thickness and Parallax

The current sensing workflow allows the Timber thickness to be changed interactively.

Thickness participates in the project measurement geometry, including compensation for the difference between the reference plane and the upper surface of the Timber.

The current operation validates that thickness:

```text
is not negative
```

and:

```text
is smaller than camera height
```

before applying it.

This physical interpretation is specific to the current eWoodX sensing setup.

---

# Timber Color

The sensing operation also samples color from the detected Timber region.

Color therefore becomes part of the project-level Timber measurement and can subsequently be included in persistent entity metadata.

Color interpretation is an application-level result rather than a responsibility of the generic camera acquisition classes.

---

# Persistent Timber Creation

A valid Timber is not automatically persisted on every frame.

Persistence occurs when the operator requests:

```text
S = save
```

and the current result is valid.

The persistence workflow is conceptually:

```text
current valid measurement
        │
        ▼
allocate Timber ID
        │
        ▼
prepare indexed metadata
        │
        ▼
EntityManager.create_entity(...)
        │
        ▼
persistent Timber directory
        │
        ▼
write sensing artifacts
```

The current indexed metadata includes configured Timber properties such as:

```text
color
length_mm
width_mm
thickness_mm
area_mm2
```

---

# Timber Entity Identity

The sensing operations use:

```python
EWoodXEntityIdAllocator
```

to generate the project-specific Timber ID.

Conceptually:

```text
EntityManager
      │
      ▼
EWoodXEntityIdAllocator
      │
      ▼
T-0001-K7M
      │
      ▼
EntityManager.create_entity(...)
```

The framework determines whether the entity exists and manages its persistent registration.

The project allocator determines the ID convention.

---

# Timber Artifacts

The current sensing operations persist the following normal entity-local artifacts:

```text
<timber-entity>/
├── entity.json
├── image.jpg
├── mask.png
├── overlay.jpg
└── measurements.json
```

`mask.png` is written when a mask is available.

The roles are:

| Artifact | Purpose |
|---|---|
| `entity.json` | Canonical framework entity manifest and metadata/state. |
| `image.jpg` | Captured source image associated with the saved Timber. |
| `mask.png` | Segmentation mask when available. |
| `overlay.jpg` | Visualized sensing/measurement result. |
| `measurements.json` | Full project-specific Timber measurement data. |

The persistent Timber entity is the authoritative project record.

---

# Persistence Sequence

The current implementation creates the persistent entity before writing all sensing artifacts.

Conceptually:

```text
allocate ID
    │
    ▼
create entity
    │
    ├── entity.json
    └── entities.db registration
    │
    ▼
write image
    │
    ▼
write mask
    │
    ▼
write overlay
    │
    ▼
write measurements.json
```

This documents the **current implementation behavior**.

It should not be interpreted as a guarantee that the persistence sequence will never evolve as the project develops.

---

# Temporary Projector Compatibility Output

The current Timber sensing operations also write a compatibility copy of the measurement to:

```text
projector_runtime/
```

using a filename following the pattern:

```text
timber_<timber_id>_measurement.json
```

The relationship is:

```text
Persistent Timber Entity
        │
        ├── authoritative measurements.json
        │
        └── compatibility copy
                    │
                    ▼
             projector_runtime/
                    │
                    ▼
           current projector workflow
```

> **Development note:** `projector_runtime` is a temporary compatibility bridge. It should not be treated as the authoritative Timber data store.

The intended longer-term direction is for design/projection workflows to obtain required entity information through the project data and distributed communication workflow.

---

# Arducam Timber Sensing

Defined in:

```text
timber_segmentation_arducam.py
```

Primary class:

```python
EWoodXTimberSegmentationArducam
```

Constructor:

```python
EWoodXTimberSegmentationArducam(
    entity_manager: EntityManager,
    intrinsic_file: Path | None = None,
)
```

The operation composes:

```text
ArducamCamera
ArducamArucoDetector
ArducamIntrinsicCalibration
ArducamExtrinsicCalibration
EntityManager
EWoodXEntityIdAllocator
eWoodX sensing configuration
```

into the complete Arducam Timber sensing workflow.

---

# Angetube Timber Sensing

Defined in:

```text
timber_segmentation_angetube.py
```

Primary class:

```python
EWoodXTimberSegmentationAngetube
```

Constructor:

```python
EWoodXTimberSegmentationAngetube(
    entity_manager: EntityManager,
    intrinsic_file: Path | None = None,
)
```

The operation composes:

```text
AngetubeCamera
AngetubeArucoDetector
AngetubeIntrinsicCalibration
AngetubeExtrinsicCalibration
EntityManager
EWoodXEntityIdAllocator
eWoodX sensing configuration
```

into the complete Angetube Timber sensing workflow.

The richer camera configuration required by the Angetube device remains encapsulated in the reusable camera implementation and project configuration rather than changing the conceptual Timber sensing workflow.

---

# Camera-Specific vs Shared Timber Logic

The current Arducam and Angetube Timber operations intentionally exist as separate project implementations.

They share the same broad workflow:

```text
capture
  ↓
undistort
  ↓
reference detection
  ↓
homography
  ↓
segmentation
  ↓
measurement
  ↓
persistence
```

but use different equipment-specific framework components and configuration.

The current code does not define a generic:

```text
BaseTimberSegmentation
TimberSegmentationManager
TimberSensorFactory
```

and this README does not imply that such an abstraction exists.

A shared abstraction should only be introduced if continued development demonstrates that it improves the project without obscuring equipment-specific behavior.

---

# Projector Operations

The current projection-related operations are:

```text
calibrate_projector_auto.py
calibrate_projector_corners.py
projector_live_viewer.py
```

They provide:

```text
projector calibration
        +
world-to-projector mapping
        +
live geometry rendering
```

for the current physical setup.

---

# Automatic Projector Calibration

Defined in:

```text
calibrate_projector_auto.py
```

Primary class:

```python
EWoodXProjectorAutoCalibration
```

The automatic calibration operation establishes the relationship between physical workspace coordinates and projector pixels using the current camera/projector setup.

Its workflow includes:

```text
load required calibration
        │
        ▼
generate projector calibration points
        │
        ▼
display projected points
        │
        ▼
capture them through the camera
        │
        ▼
detect projected dot
        │
        ▼
camera pixels → physical coordinates
        │
        ▼
physical coordinates ↔ projector pixels
        │
        ▼
calculate projector homography
        │
        ▼
save calibration
```

The operation uses the configured physical and display geometry from:

```text
projects.ewoodx.config
```

---

# Manual Projector Corner Calibration

Defined in:

```text
calibrate_projector_corners.py
```

Primary class:

```python
EWoodXProjectorCornerCalibration
```

This operation provides an alternative manual calibration workflow.

Its main responsibilities include:

```text
interactive point/corner selection
crosshair rendering
projector calibration visualization
homography calculation
calibration persistence
```

The manual workflow provides a practical alternative to automatic projector calibration for the current physical setup.

---

# Projector Calibration Output

The projector calibration is stored according to the configured mode beneath:

```text
calibration_data/
└── projector/
    ├── manual/
    └── automatic/
```

The live viewer expects a world-to-projector homography from the configured projector calibration location.

---

# Live Projector Viewer

Defined in:

```text
projector_live_viewer.py
```

Primary classes:

```python
ProjectorState
EWoodXProjectorLiveViewer
```

The live viewer receives geometry from an external application and renders it onto the calibrated physical workspace.

Its current operational role is:

```text
External Design Application
        │
        │ newline-delimited JSON / TCP
        ▼
EWoodXProjectorLiveViewer
        │
        ▼
world geometry
        │
        ▼
world-to-projector transform
        │
        ▼
projector image
        │
        ▼
physical projection
```

---

# `ProjectorState`

`ProjectorState` provides thread-safe shared state between:

```text
TCP receiving thread
        │
        ▼
shared projector state
        ▲
        │
rendering loop
```

It tracks information including:

```text
current geometry data
connection state
packet count
last received time
current Timber thickness
client address
```

Important methods include:

```python
update_from_json(...)
set_disconnected()
set_thickness(...)
get_snapshot()
```

The class allows network updates and rendering to operate concurrently without directly sharing mutable data without synchronization.

---

# `EWoodXProjectorLiveViewer`

Constructor:

```python
EWoodXProjectorLiveViewer(
    homography_file: Path | None = None,
    server_host: str | None = None,
    server_port: int | None = None,
)
```

The current default TCP server configuration is:

```text
host: 0.0.0.0
port: 9999
```

The viewer receives newline-delimited JSON geometry over TCP.

The current implementation was developed to support external geometry streaming, including the existing Grasshopper workflow.

---

# Projection State Initialization

When the viewer starts, it currently attempts to initialize its state from the latest:

```text
projector_runtime/timber_*_measurement.json
```

file.

If no compatible file exists, it starts with an empty/default state.

This is part of the current temporary projector compatibility workflow.

> **Development note:** the projector runtime lookup is not intended to become the long-term project data-access architecture.

The persistent Timber entity remains authoritative.

---

# External Geometry Stream

The live viewer runs a TCP server that accepts newline-delimited JSON messages.

Conceptually:

```text
client
  │
  │ JSON\n
  ▼
TCP socket
  │
  ▼
ProjectorState
  │
  ▼
render loop
```

The current server listens for external geometry updates and updates the shared projector state whenever a valid JSON packet is received.

This communication mechanism belongs to the current projection operation.

It is separate from the generic distributed action communication framework used by the Master and agents.

---

# Projection Geometry

The live viewer transforms geometry from physical/world millimetres into projector pixels using the calibrated homography.

Conceptually:

```text
world geometry [mm]
       │
       ▼
offset adjustment
       │
       ▼
thickness / parallax compensation
       │
       ▼
world-to-projector homography
       │
       ▼
projector pixels
```

This allows geometry generated in physical workspace coordinates to be rendered on the calibrated projector display.

---

# Projection Parallax Compensation

The live viewer uses the configured projector position and height together with Timber thickness to compensate for projection onto a surface above the calibration plane.

Conceptually:

```text
calibration plane
      │
      │ Timber thickness
      ▼
Timber top surface
      │
      ▼
geometry adjustment relative
to projector position
      │
      ▼
projector homography
```

This is project-specific physical geometry associated with the current projection setup.

---

# Rendered Geometry

The live viewer currently supports project geometry such as:

```text
Timber contour
cut geometry
mill geometry
drill / point geometry
labels
defects
```

along with rendering parameters such as:

```text
line thickness
point radius
label scale
colors
```

The exact JSON geometry structure is part of the current eWoodX projection workflow and may continue evolving with the design-side integration.

---

# Projection and Design Boundary

The current viewer should not be interpreted as the final Design framework.

Its responsibility is primarily:

```text
receive geometry
      │
      ▼
transform geometry
      │
      ▼
render geometry
      │
      ▼
project physically
```

The design application remains responsible for generating the design/manufacturing geometry itself.

Conceptually:

```text
DESIGN TOOL
    │
    └── produces geometry
            │
            ▼
PROJECTOR LIVE VIEWER
    │
    └── visualizes geometry physically
```

---

# Operation Dependencies

The current operations depend on several framework and project layers.

```text
projects.ewoodx.operations
          │
          ├── projects.ewoodx.config
          │
          ├── framework.sensing
          │
          └── framework.workspace
```

Different operations use different subsets.

For example:

```text
Camera Calibration / Setup
      │
      ├── config
      └── framework.sensing
```

```text
Timber Sensing
      │
      ├── config
      ├── framework.sensing
      ├── framework.workspace
      └── entity ID allocator
```

```text
Projection
      │
      ├── config
      ├── calibration data
      └── external geometry stream
```

---

# Operations and Entrypoints

Operations contain the actual task behavior.

Entrypoints decide how that behavior is started and composed for a user or distributed execution context.

The intended distinction is:

```text
ENTRYPOINT
    │
    ├── resolve execution context
    ├── resolve workspace / entry
    ├── choose operation
    └── start operation
            │
            ▼
        OPERATION
            │
            └── perform actual task
```

For example, the sensing entrypoint uses:

```text
EWoodXEntryAllocator
```

while resolving the project Entry and then selects an equipment-specific Timber sensing operation.

This keeps Entry context preparation separate from the Timber sensing implementation itself.

---

# Operations and Agents

Operations are also separate from distributed agents.

Conceptually:

```text
AGENT / COMMUNICATION
        │
        └── determines that work should execute
                    │
                    ▼
                ENTRYPOINT
                    │
                    ▼
                OPERATION
                    │
                    ▼
             actual project task
```

An operation should not need to own:

```text
ActionStore
AgentPoller
TCP workflow protocol
distributed lifecycle synchronization
```

Those responsibilities remain in the communication and agent layers.

---

# Operations and Orchestration

Similarly, an operation does not decide where it belongs in a larger workflow.

```text
ORCHESTRATION
      │
      └── determines what work is released
                    │
                    ▼
             distributed execution
                    │
                    ▼
                OPERATION
                    │
                    └── performs work
```

This allows the same operational capability to be invoked from different execution contexts without embedding workflow progression into the operation itself.

---

# Operations and Workspace

Operations may use the workspace framework when persistent application data is required.

For Timber sensing:

```text
operation
   │
   ▼
EntityManager
   │
   ▼
Workspace
   │
   ▼
persistent Timber entity
```

Project-specific allocation can sit around the generic workspace mechanisms:

```text
EntryManager
     │
     ▼
EWoodXEntryAllocator
     │
     ▼
project Entry

EntityManager
     │
     ▼
EWoodXEntityIdAllocator
     │
     ▼
project Entity ID
```

However, operations are not required to use `EntityManager`.

For example, calibration operations primarily produce calibration artifacts rather than application entities.

The use of workspace/entity persistence depends on the operational requirement.

---

# Current Operational Flow

The most complete current distributed sensing path can be summarized as:

```text
Application Request
        │
        ▼
eWoodX Orchestration
        │
        ▼
Generic Action
        │
        ▼
Communication Framework
        │
        ▼
Sensing Agent
        │
        ▼
Sensing Entrypoint
        │
        ├── EWoodXEntryAllocator
        │
        ▼
eWoodX Timber Sensing Operation
        │
        ├── framework.sensing
        │
        ├── eWoodX config
        │
        ├── EntityManager
        │
        └── EWoodXEntityIdAllocator
        │
        ▼
Persistent Timber Entity
```

This illustrates why the operation layer is important: it is the point where generic infrastructure becomes concrete project behavior.

---

# Current Responsibility Matrix

| Responsibility | Owner |
|---|---|
| Camera acquisition mechanism | `framework.sensing` |
| Camera calibration mathematics | `framework.sensing` |
| ArUco image detection | `framework.sensing` |
| Physical eWoodX marker arrangement | `projects.ewoodx.config` |
| Interactive calibration workflow | `projects.ewoodx.operations` |
| Angetube equipment tuning | `projects.ewoodx.operations` |
| Timber segmentation | `projects.ewoodx.operations` |
| Timber measurement | `projects.ewoodx.operations` |
| Project Entry allocation convention | `projects.ewoodx.operations` |
| Timber ID convention | `projects.ewoodx.operations` + project config |
| Generic Entry and entity persistence | `framework.workspace` |
| Timber indexed metadata schema | `projects.ewoodx.config` |
| Timber artifact creation | `projects.ewoodx.operations` |
| Projector calibration workflow | `projects.ewoodx.operations` |
| Live projector rendering | `projects.ewoodx.operations` |
| Distributed action lifecycle | `framework.communication` |
| Workflow progression | `framework.orchestration` + project orchestration definition |
| Starting/composing operations | `projects.ewoodx.entrypoints` / agents |

---

# Error and Cancellation Boundary

Operations may raise errors when physical or operational requirements cannot be satisfied.

Examples include:

```text
missing calibration files
camera acquisition failure
invalid calibration data
missing reference markers
invalid physical values
file persistence failure
```

The operation itself owns detection of the operational failure.

When an operation is executed as part of a distributed action, translating that outcome into:

```text
COMPLETED
FAILED
CANCELLED
```

belongs to the surrounding execution/communication layer.

This preserves the framework principle:

> **Status ownership follows execution ownership.**

---

# Units

The current operations primarily use:

```text
physical coordinates     → millimetres
length / width / height  → millimetres
area                     → square millimetres
image coordinates        → pixels
projector coordinates    → pixels
camera/projector images  → pixel arrays
```

Names such as:

```text
length_mm
width_mm
thickness_mm
area_mm2
contour_mm
corners_mm
```

make these units explicit in persisted and streamed project data.

---

# Development Principles

When adding or modifying an eWoodX operation:

1. Keep reusable mechanisms in `framework`.
2. Keep eWoodX-specific operational meaning in `projects.ewoodx.operations`.
3. Obtain project-specific constants from `projects.ewoodx.config`.
4. Keep distributed action lifecycle outside the operation.
5. Keep workflow progression outside the operation.
6. Use the workspace framework for persistent project data when appropriate.
7. Keep project-specific identity/allocation conventions outside the generic workspace framework.
8. Preserve clear equipment-specific behavior where hardware requirements differ.
9. Avoid premature base classes or manager abstractions.
10. Document temporary compatibility mechanisms explicitly.
11. Generalize behavior only after repeated implementation demonstrates a stable reusable boundary.

---

# Ongoing Development

The operations package represents the **current operational state** of eWoodX and is not final.

Current development is concentrated primarily around:

```text
sensing
Timber data
projection
distributed execution integration
```

Future development may introduce operations associated with:

```text
design workflows
entity query and retrieval
additional sensing equipment
additional material interpretation
robot control
fabrication
additional projection workflows
other physical-digital processes
```

These future areas should be introduced according to actual project requirements rather than being predefined as complete abstractions before implementation.

The current package structure may therefore evolve as the project grows.

---

# Summary

`projects.ewoodx.operations` is the concrete execution layer of the eWoodX application.

It currently connects:

```text
                     CONFIG
                       │
                       ▼
FRAMEWORK ───────► OPERATIONS ◄────── PROJECT SEMANTICS
                       │
                       ▼
               PHYSICAL / DIGITAL
                    SYSTEMS
```

Its current operational areas are:

```text
OPERATIONS
    │
    ├── Project Identity / Allocation
    │
    ├── Camera Calibration / Setup
    │
    ├── Timber Sensing
    │
    └── Projection
```

The central architectural boundary is:

```text
FRAMEWORK
    │
    └── reusable capabilities

CONFIG
    │
    └── eWoodX-specific parameters

OPERATIONS
    │
    └── eWoodX-specific executable behavior

ENTRYPOINTS / AGENTS
    │
    └── determine how that behavior is started
```

The package is expected to continue developing as additional eWoodX capabilities move from experimentation into established project operations.