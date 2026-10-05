# Arducam Camera Framework

The `framework.sensing.cameras.arducam` package provides reusable camera acquisition, intrinsic calibration, ArUco marker detection, and planar extrinsic calibration tools for an Arducam camera accessed through OpenCV.

The package separates four responsibilities:

```text
ArducamCamera
    │
    └── camera acquisition

ArducamIntrinsicCalibration
    │
    └── camera intrinsics + distortion

ArducamArucoDetector
    │
    └── marker detection in image coordinates

ArducamExtrinsicCalibration
    │
    └── planar pixel → physical coordinate mapping
```

The package-level public API is:

```python
from framework.sensing.cameras.arducam import (
    ArducamCamera,
    ArducamIntrinsicCalibration,
    ArducamExtrinsicCalibration,
    ArducamArucoDetector,
)
```

These components can be used independently or combined into a camera calibration and sensing workflow.

---

# Purpose

The Arducam package provides the reusable camera-specific functionality required to convert raw camera images into calibrated image-space and planar physical-space information.

A typical workflow is:

```text
ArducamCamera
      │
      ▼
raw image
      │
      ▼
ArducamIntrinsicCalibration
      │
      ├── camera matrix
      ├── distortion coefficients
      └── undistorted image
                │
                ▼
       ArducamArucoDetector
                │
                ▼
        marker pixel corners
                │
                │ application supplies
                │ physical correspondence
                ▼
    ArducamExtrinsicCalibration
                │
                ▼
     pixel → physical coordinates
               (mm)
```

The package deliberately keeps camera functionality separate from application-specific sensing logic.

It does not determine what detected markers represent, how a physical workspace is arranged, what objects should be measured, or how sensing results should be persisted.

---

# Responsibility

The package provides:

- OpenCV-based Arducam acquisition;
- camera opening and closing;
- optional acquisition resolution configuration;
- frame capture;
- checkerboard-based intrinsic calibration;
- camera matrix and distortion estimation;
- intrinsic calibration persistence;
- image undistortion;
- ArUco marker detection;
- marker ID and pixel-corner extraction;
- planar homography calibration;
- pixel-to-physical coordinate transformation;
- homography persistence;
- calibration reports;
- reprojection error calculation for planar calibration.

The package does **not**:

- define application-specific marker layouts;
- assign physical coordinates to ArUco marker IDs;
- define workspace geometry;
- identify application-specific objects;
- perform object segmentation;
- calculate application-specific dimensions;
- manage sensing sessions;
- create workspace entries;
- create persistent entities;
- define communication actions;
- control distributed sensing agents;
- define a generic 3D camera pose calibration.

Those responsibilities belong to higher-level application or framework components.

---

# Package Structure

```text
arducam/
├── __init__.py
├── camera.py
├── intrinsic_calibration.py
├── extrinsic_calibration.py
└── aruco_detector.py
```

The package exports:

```text
camera.py
    └── ArducamCamera

intrinsic_calibration.py
    └── ArducamIntrinsicCalibration

extrinsic_calibration.py
    └── ArducamExtrinsicCalibration

aruco_detector.py
    └── ArducamArucoDetector
```

---

# Component Boundaries

The four public classes deliberately solve different problems.

```text
CAMERA HARDWARE
      │
      ▼
ArducamCamera
      │
      ▼
pixel image
      │
      ├─────────────────────────────┐
      │                             │
      ▼                             ▼
Intrinsic Calibration       ArUco Detection
      │                             │
      ▼                             ▼
camera model                 marker pixel corners
                                    │
                                    │
                                    ▼
                           physical correspondence
                           supplied externally
                                    │
                                    ▼
                         Extrinsic Calibration
                                    │
                                    ▼
                         planar physical space
```

In particular:

```text
ArducamArucoDetector
        ≠
physical marker layout
```

and:

```text
ArducamExtrinsicCalibration
        ≠
ArUco detection
```

The detector identifies marker corners in image coordinates.

The extrinsic calibration receives already-established pixel-to-physical point correspondences.

This keeps the camera framework independent of a particular physical calibration setup.

---

# ArducamCamera

```python
class ArducamCamera
```

`ArducamCamera` provides a small OpenCV-based interface for camera acquisition.

Its responsibility is limited to:

```text
open camera
configure resolution
capture frame
inspect actual resolution
close camera
```

It does not perform calibration, marker detection, or image analysis.

---

## Constructor

```python
ArducamCamera(
    camera_index: int,
    width: int | None = None,
    height: int | None = None,
    backend: int | None = cv2.CAP_DSHOW,
)
```

Example:

```python
from framework.sensing.cameras.arducam import (
    ArducamCamera,
)

camera = ArducamCamera(
    camera_index=0,
    width=1920,
    height=1080,
)
```

---

## `camera_index`

```python
camera.camera_index
```

The OpenCV camera device index.

It must be an integer.

For example:

```python
camera_index=0
```

selects camera index `0`.

A non-integer value raises `TypeError`.

---

## `width`

```python
camera.width
```

Optional requested acquisition width.

If supplied, the value must be greater than zero.

The value is requested from the camera when `open()` is called.

It does not guarantee that the camera or backend will actually provide that exact resolution.

---

## `height`

```python
camera.height
```

Optional requested acquisition height.

If supplied, it must be greater than zero.

Like `width`, it represents a requested acquisition setting.

---

## `backend`

```python
camera.backend
```

Optional OpenCV capture backend.

The default is:

```python
cv2.CAP_DSHOW
```

If:

```python
backend=None
```

the camera is opened without explicitly specifying an OpenCV backend:

```python
cv2.VideoCapture(camera_index)
```

This allows backend selection to be adapted to the operating environment.

---

# Camera State

## `is_open`

```python
camera.is_open -> bool
```

Read-only property indicating whether an active OpenCV capture object exists and reports itself as open.

Example:

```python
if camera.is_open:
    print("Camera is open")
```

Before `open()`:

```python
camera.is_open == False
```

After a successful `open()`:

```python
camera.is_open == True
```

---

# Opening the Camera

## `open()`

```python
camera.open() -> None
```

Opens the configured camera.

Example:

```python
camera.open()
```

The method:

```text
create cv2.VideoCapture
        │
        ▼
verify camera opened
        │
        ▼
request width if configured
        │
        ▼
request height if configured
        │
        ▼
store active capture
```

If the camera is already open:

```python
camera.open()
```

returns without reopening it.

If OpenCV cannot open the requested device, `RuntimeError` is raised.

---

# Actual Camera Resolution

## `resolution`

```python
camera.resolution -> tuple[int, int]
```

Returns the actual current OpenCV capture resolution as:

```text
(width, height)
```

Example:

```python
width, height = camera.resolution
```

This distinction is useful because:

```text
camera.width / camera.height
        │
        └── requested configuration

camera.resolution
        │
        └── actual current capture resolution
```

A camera or backend may not accept the exact requested values.

The camera must be open before this property is accessed.

Otherwise `RuntimeError` is raised.

---

# Capturing a Frame

## `capture()`

```python
camera.capture() -> numpy.ndarray
```

Captures one frame from the camera.

Example:

```python
frame = camera.capture()
```

The returned frame is the image produced by OpenCV.

The camera must already be open.

If the camera is not open:

```text
RuntimeError
```

is raised.

If OpenCV fails to acquire a valid frame, `RuntimeError` is also raised.

---

# Closing the Camera

## `close()`

```python
camera.close() -> None
```

Releases the OpenCV capture object.

Example:

```python
camera.close()
```

After closing:

```python
camera.is_open == False
```

Calling `close()` when no active capture exists is safe.

---

# Basic Acquisition Example

```python
from framework.sensing.cameras.arducam import (
    ArducamCamera,
)

camera = ArducamCamera(
    camera_index=0,
    width=1920,
    height=1080,
)

camera.open()

try:
    print(camera.resolution)

    frame = camera.capture()

finally:
    camera.close()
```

The `try/finally` structure ensures that the camera is released even if later processing fails.

---

# ArducamIntrinsicCalibration

```python
class ArducamIntrinsicCalibration
```

`ArducamIntrinsicCalibration` performs checkerboard-based intrinsic camera calibration.

It estimates:

```text
camera matrix
      +
distortion coefficients
      +
image size
      +
RMS reprojection error
```

using OpenCV's standard camera calibration model.

The current implementation uses:

```python
cv2.calibrateCamera(...)
```

Therefore the calibration is based on the standard OpenCV pinhole camera model.

It is not a fisheye calibration model.

---

# Intrinsic Calibration Model

The camera matrix has the standard form:

```text
      [ fx   0   cx ]
K  =  [  0  fy   cy ]
      [  0   0    1 ]
```

where:

```text
fx, fy
    │
    └── focal lengths in pixel units

cx, cy
    │
    └── principal point
```

The distortion coefficients are returned by OpenCV and stored together with the camera matrix.

---

# Intrinsic Constructor

```python
ArducamIntrinsicCalibration(
    checkerboard_inner_corners: tuple[int, int],
    square_size_mm: float,
)
```

Example:

```python
from framework.sensing.cameras.arducam import (
    ArducamIntrinsicCalibration,
)

calibration = ArducamIntrinsicCalibration(
    checkerboard_inner_corners=(9, 6),
    square_size_mm=25.0,
)
```

---

## `checkerboard_inner_corners`

```python
calibration.checkerboard_inner_corners
```

Stores:

```text
(columns, rows)
```

of checkerboard **inner corners**.

Both values must be greater than zero.

The values are normalized to integers.

---

## `square_size_mm`

```python
calibration.square_size_mm
```

Physical checkerboard square size in millimetres.

The value must be greater than zero and is stored as a float.

This value establishes the physical scale of the checkerboard object points used during calibration.

---

# Intrinsic Calibration Results

The following public attributes are initialized as:

```python
calibration.camera_matrix = None
calibration.dist_coeffs = None
calibration.image_size = None
calibration.rms_error = None

calibration.accepted_images = 0
calibration.total_images = 0
```

After successful calibration:

```text
camera_matrix
    │
    └── intrinsic camera matrix

dist_coeffs
    │
    └── OpenCV distortion coefficients

image_size
    │
    └── calibration image size as (width, height)

rms_error
    │
    └── RMS reprojection error

accepted_images
    │
    └── images where checkerboard detection succeeded

total_images
    │
    └── number of supplied image paths
```

---

# Intrinsic Calibration State

## `is_calibrated`

```python
calibration.is_calibrated -> bool
```

Returns `True` only when all required calibration results exist:

```text
camera_matrix
dist_coeffs
image_size
rms_error
```

Before calibration:

```python
calibration.is_calibrated == False
```

After successful calibration:

```python
calibration.is_calibrated == True
```

A successfully loaded calibration is also considered calibrated.

---

# Performing Intrinsic Calibration

## `calibrate()`

```python
calibration.calibrate(
    image_paths: Iterable[str | Path],
) -> None
```

Example:

```python
calibration.calibrate(
    [
        "calibration/image_01.jpg",
        "calibration/image_02.jpg",
        "calibration/image_03.jpg",
    ]
)
```

The process is:

```text
calibration image paths
        │
        ▼
read each image
        │
        ▼
convert to grayscale
        │
        ▼
find checkerboard corners
        │
        ▼
refine corners
        │
        ▼
collect image/object points
        │
        ▼
cv2.calibrateCamera()
        │
        ▼
store calibration results
```

---

# Checkerboard Object Points

The physical checkerboard model is generated in millimetres.

Conceptually:

```text
(0, 0)
(square_size, 0)
(2 × square_size, 0)
...
```

with:

```text
Z = 0
```

for all checkerboard points.

The supplied `square_size_mm` therefore determines the physical scale used by the intrinsic calibration object points.

---

# Image Acceptance

Not every supplied image is necessarily used.

An image is accepted only when:

```python
cv2.findChessboardCorners(...)
```

successfully detects the configured checkerboard.

Detected corners are refined using:

```python
cv2.cornerSubPix(...)
```

The calibration object records:

```python
calibration.total_images
calibration.accepted_images
```

so the caller can inspect how much of the calibration dataset was actually used.

Images that cannot be read are skipped.

Images where the checkerboard is not detected are also skipped.

If no supplied image produces a valid checkerboard detection, `RuntimeError` is raised.

---

# Calibration Image Resolution

All readable calibration images must have the same resolution.

The first readable image establishes:

```python
calibration.image_size
```

as:

```text
(width, height)
```

If a later readable image has a different resolution:

```text
ValueError
```

is raised.

This protects the calibration from mixing incompatible camera image sizes.

---

# Undistortion

## `undistort()`

```python
calibration.undistort(
    image: numpy.ndarray,
) -> numpy.ndarray
```

Returns an undistorted image using:

```python
cv2.undistort(...)
```

with the stored:

```text
camera_matrix
dist_coeffs
```

Example:

```python
undistorted = calibration.undistort(
    frame
)
```

A calibration must already have been computed or loaded.

Otherwise `RuntimeError` is raised.

The current method does not crop the image or calculate a new optimized camera matrix.

---

# Saving Intrinsic Calibration

## `save()`

```python
calibration.save(
    file_path: str | Path,
) -> None
```

Saves machine-readable calibration data to an NPZ file.

Example:

```python
calibration.save(
    "calibration/camera_intrinsics.npz"
)
```

Parent directories are created automatically.

The stored data include:

```text
camera_matrix
dist_coeffs
image_size
rms_error
checkerboard_inner_corners
square_size_mm
```

A valid calibration must exist before saving.

Otherwise `RuntimeError` is raised.

---

# Intrinsic Text Report

## `save_text_report()`

```python
calibration.save_text_report(
    file_path: str | Path,
) -> None
```

Writes a human-readable calibration report.

Example:

```python
calibration.save_text_report(
    "calibration/camera_intrinsics.txt"
)
```

The report includes:

```text
calibration model
checkerboard inner corners
checkerboard square size
accepted image count
total image count
image resolution
RMS reprojection error
camera matrix
distortion coefficients
```

The report is intended for inspection and documentation.

The NPZ file remains the machine-readable calibration representation used by `load()`.

---

# Loading Intrinsic Calibration

## `load()`

```python
ArducamIntrinsicCalibration.load(
    file_path: str | Path,
) -> ArducamIntrinsicCalibration
```

This is a class method.

Example:

```python
calibration = (
    ArducamIntrinsicCalibration.load(
        "calibration/camera_intrinsics.npz"
    )
)
```

The method reconstructs:

```text
checkerboard configuration
square size
camera matrix
distortion coefficients
image size
RMS error
```

from the NPZ file.

If the file does not exist:

```text
FileNotFoundError
```

is raised.

After loading:

```python
calibration.is_calibrated == True
```

provided the expected calibration data are present.

---

# Intrinsic Calibration Example

```python
from pathlib import Path

from framework.sensing.cameras.arducam import (
    ArducamIntrinsicCalibration,
)

calibration = ArducamIntrinsicCalibration(
    checkerboard_inner_corners=(9, 6),
    square_size_mm=25.0,
)

images = sorted(
    Path("calibration/images").glob("*.jpg")
)

calibration.calibrate(images)

print(
    "Accepted:",
    calibration.accepted_images,
    "/",
    calibration.total_images,
)

print(
    "RMS:",
    calibration.rms_error,
)

calibration.save(
    "calibration/camera_intrinsics.npz"
)

calibration.save_text_report(
    "calibration/camera_intrinsics.txt"
)
```

---

# ArducamArucoDetector

```python
class ArducamArucoDetector
```

`ArducamArucoDetector` detects ArUco markers in an image.

Its responsibility is deliberately limited to:

```text
image
   │
   ▼
ArUco detection
   │
   ▼
marker ID
   +
four image-space corners
```

It does not assign physical-world coordinates to those markers.

---

# Detector Constructor

```python
ArducamArucoDetector(
    dictionary_name: str,
)
```

Example:

```python
from framework.sensing.cameras.arducam import (
    ArducamArucoDetector,
)

detector = ArducamArucoDetector(
    dictionary_name="DICT_4X4_50",
)
```

`dictionary_name` must correspond to an ArUco dictionary exposed by:

```python
cv2.aruco
```

If the value is not a string:

```text
TypeError
```

is raised.

If the named dictionary does not exist:

```text
ValueError
```

is raised.

---

# Detector Public Attributes

The detector exposes:

```python
detector.dictionary_name
detector.dictionary
detector.parameters
detector.detector
```

These correspond to:

```text
dictionary_name
    │
    └── configured OpenCV dictionary name

dictionary
    │
    └── predefined OpenCV ArUco dictionary

parameters
    │
    └── cv2.aruco.DetectorParameters

detector
    │
    └── cv2.aruco.ArucoDetector
```

The current implementation uses default OpenCV detector parameters.

---

# Detecting Markers

## `detect()`

```python
detector.detect(
    image,
) -> dict[int, numpy.ndarray]
```

Example:

```python
markers = detector.detect(
    image
)
```

The input may be:

```text
BGR image
    or
grayscale image
```

A BGR image is converted internally to grayscale.

A grayscale image is used directly.

Other dimensionalities raise `ValueError`.

Passing:

```python
None
```

also raises `ValueError`.

---

# Detection Result

If markers are found, the returned dictionary is structured as:

```python
{
    marker_id: corners,
}
```

where each `corners` value is a NumPy array containing the four detected image-space marker corners.

Conceptually:

```python
{
    0: [
        [x0, y0],
        [x1, y1],
        [x2, y2],
        [x3, y3],
    ],
    1: [
        ...
    ],
}
```

The corner arrays use:

```python
dtype=np.float32
```

and have shape:

```text
(4, 2)
```

for a normal ArUco marker.

If no markers are detected:

```python
{}
```

is returned.

This makes absence of detections a normal result rather than an exception.

---

# Marker Detection Boundary

The detector answers:

```text
Which marker IDs are visible?

Where are their corners in the image?
```

It does **not** answer:

```text
Where is this marker physically located?

What physical point does this corner represent?

Which marker defines the workspace origin?

How large is the calibrated workspace?
```

Those relationships are application-specific.

For example:

```text
ArUco detection

marker 10
    └── pixel corners

marker 11
    └── pixel corners

marker 12
    └── pixel corners
```

may later be interpreted by an application as:

```text
marker 10 → physical reference A
marker 11 → physical reference B
marker 12 → physical reference C
```

That interpretation deliberately remains outside `ArducamArucoDetector`.

---

# ArUco Detection Example

```python
from framework.sensing.cameras.arducam import (
    ArducamArucoDetector,
)

detector = ArducamArucoDetector(
    dictionary_name="DICT_4X4_50",
)

markers = detector.detect(
    image
)

for marker_id, corners in markers.items():
    print(
        marker_id,
        corners,
    )
```

---

# ArducamExtrinsicCalibration

```python
class ArducamExtrinsicCalibration
```

`ArducamExtrinsicCalibration` provides planar homography-based calibration.

Despite the class name `ExtrinsicCalibration`, the current implementation specifically computes:

> a 2D projective mapping from image pixel coordinates to physical planar coordinates in millimetres.

Conceptually:

```text
IMAGE SPACE                     PHYSICAL PLANE

(x_pixel, y_pixel)
        │
        │ homography H
        ▼
(x_mm, y_mm)
```

This is not a generic six-degree-of-freedom camera extrinsic pose.

It does not compute:

```text
3D rotation
3D translation
camera-to-world SE(3) transform
```

Its intended geometry is planar.

---

# Extrinsic Constructor

```python
ArducamExtrinsicCalibration()
```

Example:

```python
from framework.sensing.cameras.arducam import (
    ArducamExtrinsicCalibration,
)

calibration = ArducamExtrinsicCalibration()
```

Initial state:

```python
calibration.homography = None
calibration.reprojection_errors_mm = None
```

---

# Extrinsic Calibration State

## `is_calibrated`

```python
calibration.is_calibrated -> bool
```

Returns:

```python
True
```

when a homography is available.

Before calibration:

```python
False
```

After `calibrate()` or `load()`:

```python
True
```

---

# Computing the Homography

## `calibrate()`

```python
calibration.calibrate(
    pixel_points,
    world_points_mm,
)
```

The method returns the calculated homography matrix.

Inputs are converted internally to:

```python
numpy.float32
```

---

## Pixel Points

`pixel_points` must have shape:

```text
(N, 2)
```

For example:

```python
pixel_points = [
    [120.0, 80.0],
    [1820.0, 85.0],
    [1810.0, 990.0],
    [125.0, 995.0],
]
```

These points represent locations in the camera image.

---

## Physical Points

`world_points_mm` must also have shape:

```text
(N, 2)
```

For example:

```python
world_points_mm = [
    [0.0, 0.0],
    [1000.0, 0.0],
    [1000.0, 500.0],
    [0.0, 500.0],
]
```

These points represent corresponding locations on the physical calibration plane in millimetres.

---

# Correspondence Requirements

Calibration requires:

```text
pixel_points.shape = (N, 2)

world_points_mm.shape = (N, 2)

same N for both sets

N >= 4
```

At least four point correspondences are required for the planar homography.

Invalid point shapes raise `ValueError`.

Different point counts raise `ValueError`.

Fewer than four correspondences raise `ValueError`.

---

# Homography Calculation

The current implementation uses:

```python
cv2.findHomography(
    pixel_points,
    world_points_mm,
    method=0,
)
```

Therefore the mapping is calculated directly from the supplied correspondences without a robust RANSAC method.

If OpenCV cannot calculate a homography:

```text
RuntimeError
```

is raised.

The resulting matrix is stored in:

```python
calibration.homography
```

---

# Reprojection Errors

After calibration, the original pixel calibration points are transformed back into physical coordinates using the computed homography.

For each point:

```text
predicted physical point
           │
           ▼
difference from supplied physical point
           │
           ▼
Euclidean distance
           │
           ▼
reprojection error in mm
```

The results are stored in:

```python
calibration.reprojection_errors_mm
```

There is one error value for each calibration correspondence.

This provides a direct indication of how closely the planar homography reproduces the supplied calibration points.

---

# Transforming Pixel Coordinates

## `transform_points()`

```python
calibration.transform_points(
    pixel_points,
)
```

Transforms image coordinates into calibrated planar physical coordinates.

Example:

```python
physical_points = (
    calibration.transform_points(
        [
            [500.0, 300.0],
            [900.0, 600.0],
        ]
    )
)
```

Input shape must be:

```text
(N, 2)
```

The returned NumPy array also has shape:

```text
(N, 2)
```

and represents:

```text
(x_mm, y_mm)
```

according to the physical coordinate system used during calibration.

The method internally uses:

```python
cv2.perspectiveTransform(...)
```

A homography must already exist.

Otherwise `RuntimeError` is raised.

---

# Physical Coordinate System

The extrinsic calibration does not define the physical coordinate system itself.

The supplied:

```python
world_points_mm
```

define that coordinate system.

For example:

```python
[
    [0.0, 0.0],
    [1000.0, 0.0],
    [1000.0, 500.0],
    [0.0, 500.0],
]
```

defines a planar physical frame with:

```text
origin
    │
    └── first chosen physical reference

X direction
    │
    └── determined by supplied coordinates

Y direction
    │
    └── determined by supplied coordinates

scale
    │
    └── millimetres
```

The framework does not decide which physical reference points should receive those coordinates.

---

# Saving Extrinsic Calibration

## `save()`

```python
calibration.save(
    file_path,
) -> None
```

Saves the homography to an NPZ file.

Example:

```python
calibration.save(
    "calibration/camera_extrinsics.npz"
)
```

The stored machine-readable data contain:

```text
homography
```

Parent directories are created automatically.

A calibration must exist before saving.

Otherwise `RuntimeError` is raised.

---

# Extrinsic Text Report

## `save_text_report()`

```python
calibration.save_text_report(
    file_path: str | Path,
    pixel_points=None,
    world_points_mm=None,
) -> None
```

Writes a human-readable planar calibration report.

Example:

```python
calibration.save_text_report(
    "calibration/camera_extrinsics.txt",
    pixel_points=pixel_points,
    world_points_mm=world_points_mm,
)
```

The report always contains:

```text
homography matrix
```

If supplied, it also includes:

```text
pixel calibration points
world calibration points
```

If reprojection errors were calculated during the current calibration operation, the report includes:

```text
reprojection error for each point
```

A valid homography must exist before the report can be written.

---

# Loading Extrinsic Calibration

## `load()`

```python
ArducamExtrinsicCalibration.load(
    file_path,
)
```

Loads a previously saved homography.

Example:

```python
calibration = (
    ArducamExtrinsicCalibration.load(
        "calibration/camera_extrinsics.npz"
    )
)
```

If the file does not exist:

```text
FileNotFoundError
```

is raised.

The loaded instance receives:

```python
calibration.homography
```

and therefore:

```python
calibration.is_calibrated == True
```

The current saved NPZ representation contains only the homography.

Consequently, `reprojection_errors_mm` are not restored by `load()`.

---

# Extrinsic Calibration Example

```python
import numpy as np

from framework.sensing.cameras.arducam import (
    ArducamExtrinsicCalibration,
)

pixel_points = np.array(
    [
        [120.0, 80.0],
        [1820.0, 85.0],
        [1810.0, 990.0],
        [125.0, 995.0],
    ],
    dtype=np.float32,
)

world_points_mm = np.array(
    [
        [0.0, 0.0],
        [1000.0, 0.0],
        [1000.0, 500.0],
        [0.0, 500.0],
    ],
    dtype=np.float32,
)

calibration = (
    ArducamExtrinsicCalibration()
)

homography = calibration.calibrate(
    pixel_points=pixel_points,
    world_points_mm=world_points_mm,
)

print(homography)

print(
    calibration.reprojection_errors_mm
)

calibration.save(
    "calibration/camera_extrinsics.npz"
)

calibration.save_text_report(
    "calibration/camera_extrinsics.txt",
    pixel_points=pixel_points,
    world_points_mm=world_points_mm,
)
```

---

# Combining ArUco Detection and Planar Calibration

`ArducamArucoDetector` and `ArducamExtrinsicCalibration` can be combined, but the physical correspondence between them must be supplied by the application.

Conceptually:

```text
image
  │
  ▼
ArducamArucoDetector
  │
  ▼
{
    marker_id: pixel corners
}
  │
  │
  │ application knows physical marker layout
  ▼
pixel_points + world_points_mm
  │
  ▼
ArducamExtrinsicCalibration
  │
  ▼
homography
```

For example, an application may know that selected detected marker corners correspond to:

```text
pixel corner A → (0, 0) mm
pixel corner B → (1000, 0) mm
pixel corner C → (1000, 500) mm
pixel corner D → (0, 500) mm
```

The application constructs those correspondence arrays and passes them to:

```python
calibration.calibrate(
    pixel_points,
    world_points_mm,
)
```

The generic detector itself does not contain those assumptions.

---

# Intrinsic and Extrinsic Calibration

The two calibration classes solve different geometric problems.

```text
INTRINSIC CALIBRATION

checkerboard images
       │
       ▼
camera matrix
       +
distortion coefficients
       │
       ▼
undistorted image
```

versus:

```text
PLANAR EXTRINSIC CALIBRATION

pixel coordinates
       +
physical planar coordinates
       │
       ▼
homography
       │
       ▼
pixel → millimetre mapping
```

Conceptually:

```text
raw camera image
       │
       ▼
intrinsic calibration
       │
       ▼
corrected image geometry
       │
       ▼
planar extrinsic calibration
       │
       ▼
physical planar coordinates
```

The current classes remain independent so that calibration data can be generated, saved, loaded, and applied separately.

---

# Complete Usage Flow

A higher-level application can combine the package components as follows:

```text
1. Open camera
       │
       ▼
2. Capture image
       │
       ▼
3. Apply intrinsic undistortion
       │
       ▼
4. Detect ArUco markers
       │
       ▼
5. Application resolves physical
   marker correspondences
       │
       ▼
6. Compute/load planar homography
       │
       ▼
7. Transform relevant pixel points
   into physical millimetres
       │
       ▼
8. Higher-level sensing operation
   interprets the result
```

Example:

```python
from framework.sensing.cameras.arducam import (
    ArducamCamera,
    ArducamIntrinsicCalibration,
    ArducamExtrinsicCalibration,
    ArducamArucoDetector,
)

camera = ArducamCamera(
    camera_index=0,
)

intrinsics = (
    ArducamIntrinsicCalibration.load(
        "calibration/camera_intrinsics.npz"
    )
)

extrinsics = (
    ArducamExtrinsicCalibration.load(
        "calibration/camera_extrinsics.npz"
    )
)

detector = ArducamArucoDetector(
    dictionary_name="DICT_4X4_50",
)

camera.open()

try:
    frame = camera.capture()

    undistorted = intrinsics.undistort(
        frame
    )

    markers = detector.detect(
        undistorted
    )

    # Higher-level application logic determines
    # which detected image points should be
    # transformed or how marker IDs correspond
    # to physical references.

finally:
    camera.close()
```

---

# Calibration Persistence

The package separates machine-readable calibration files from human-readable reports.

```text
MACHINE-READABLE

intrinsic .npz
    │
    ├── camera matrix
    ├── distortion coefficients
    ├── image size
    ├── RMS error
    ├── checkerboard configuration
    └── square size

extrinsic .npz
    │
    └── homography
```

and:

```text
HUMAN-READABLE

intrinsic text report
extrinsic text report
```

The NPZ files are intended for loading calibration data back into the framework.

The text reports are intended for inspection, validation, and documentation.

---

# Coordinate Units

The package uses different coordinate units at different stages:

```text
image coordinates
    │
    └── pixels

checkerboard physical geometry
    │
    └── millimetres

planar world coordinates
    │
    └── millimetres

planar reprojection errors
    │
    └── millimetres

intrinsic RMS reprojection error
    │
    └── pixel-space calibration error
```

Maintaining this distinction is important when combining intrinsic and planar calibration results.

---

# Error and Validation Behavior

The public classes validate their immediate inputs rather than silently accepting invalid configurations.

Typical errors include:

| Condition | Error |
|---|---|
| Non-integer camera index | `TypeError` |
| Non-positive requested width/height | `ValueError` |
| Camera cannot open | `RuntimeError` |
| Capture requested while camera is closed | `RuntimeError` |
| Frame acquisition fails | `RuntimeError` |
| Invalid checkerboard dimensions | `ValueError` |
| Non-positive checkerboard square size | `ValueError` |
| No intrinsic calibration images | `ValueError` |
| Mixed readable calibration image resolutions | `ValueError` |
| Checkerboard detected in no images | `RuntimeError` |
| Intrinsic operation requiring unavailable calibration | `RuntimeError` |
| Missing calibration file | `FileNotFoundError` |
| Unknown ArUco dictionary | `ValueError` |
| Invalid detector image | `ValueError` |
| Invalid homography point shape | `ValueError` |
| Unequal correspondence counts | `ValueError` |
| Fewer than four planar correspondences | `ValueError` |
| Homography cannot be computed | `RuntimeError` |
| Extrinsic operation before calibration | `RuntimeError` |

Higher-level applications can decide how these failures should affect their own workflow.

---

# Relationship to Higher-Level Sensing

This package provides camera-level capabilities.

A higher-level sensing operation may build on it:

```text
CAMERA FRAMEWORK

camera acquisition
intrinsic calibration
ArUco detection
planar calibration
        │
        ▼
APPLICATION SENSING

workspace selection
session/entry selection
object segmentation
measurement
object identity
artifact generation
persistence
```

The Arducam package should therefore remain independent of:

```text
workspace naming
entity schemas
object types
distributed actions
agent identities
application-specific measurement logic
```

This separation allows the same camera functionality to be reused by different applications.

---

# Public API

The supported package-level imports are:

```python
from framework.sensing.cameras.arducam import (
    ArducamCamera,
    ArducamIntrinsicCalibration,
    ArducamExtrinsicCalibration,
    ArducamArucoDetector,
)
```

| Public object | Responsibility |
|---|---|
| `ArducamCamera` | Open, configure, capture from, and close the camera. |
| `ArducamIntrinsicCalibration` | Compute, persist, load, and apply intrinsic camera calibration. |
| `ArducamExtrinsicCalibration` | Compute, persist, load, and apply planar pixel-to-physical homography calibration. |
| `ArducamArucoDetector` | Detect ArUco marker IDs and image-space marker corners. |

Internal implementation details and underscore-prefixed helpers are not part of the public API.

---

# Summary

The Arducam camera package establishes four reusable capabilities:

```text
ArducamCamera
      │
      ▼
camera image

ArducamIntrinsicCalibration
      │
      ▼
calibrated image geometry

ArducamArucoDetector
      │
      ▼
marker IDs + pixel corners

ArducamExtrinsicCalibration
      │
      ▼
planar physical coordinates
```

Their responsibilities remain deliberately separate:

```text
camera acquisition
        ≠
intrinsic calibration
        ≠
marker detection
        ≠
physical marker interpretation
        ≠
planar coordinate calibration
        ≠
application sensing logic
```

The package therefore provides reusable camera and calibration primitives while leaving physical setup interpretation and sensing semantics to higher-level application code.