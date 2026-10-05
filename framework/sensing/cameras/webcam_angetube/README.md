# Angetube Webcam Framework

The `framework.sensing.cameras.webcam_angetube` package provides reusable camera acquisition, hardware/property control, intrinsic calibration, ArUco marker detection, and planar extrinsic calibration tools for the Angetube webcam.

The package separates four primary responsibilities:

```text
AngetubeCamera
    │
    ├── camera acquisition
    ├── stream configuration
    ├── camera property control
    ├── optional duvc_ctl hardware control
    └── digital zoom

AngetubeIntrinsicCalibration
    │
    ├── standard pinhole calibration
    ├── fisheye calibration
    └── image undistortion

AngetubeArucoDetector
    │
    └── marker detection in image coordinates

AngetubeExtrinsicCalibration
    │
    └── planar pixel → physical coordinate mapping
```

The package-level public API is:

```python
from framework.sensing.cameras.webcam_angetube import (
    AngetubeCamera,
    AngetubeIntrinsicCalibration,
    AngetubeExtrinsicCalibration,
    AngetubeArucoDetector,
)
```

These components can be used independently or combined into a calibrated camera sensing workflow.

---

# Purpose

The Angetube package provides the reusable camera-specific functionality required to acquire controlled webcam images and convert image-space information into calibrated planar physical-space information.

A typical workflow is:

```text
AngetubeCamera
      │
      ├── stream configuration
      ├── focus / exposure / image properties
      └── optional digital zoom
      │
      ▼
raw image
      │
      ▼
AngetubeIntrinsicCalibration
      │
      ├── camera matrix
      ├── distortion coefficients
      └── undistorted image
                │
                ▼
       AngetubeArucoDetector
                │
                ▼
        marker pixel corners
                │
                │ application supplies
                │ physical correspondence
                ▼
    AngetubeExtrinsicCalibration
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

- OpenCV-based webcam acquisition;
- stream resolution configuration;
- FPS and FOURCC configuration;
- autofocus and manual-focus configuration;
- automatic and manual exposure configuration;
- brightness, contrast, saturation, sharpness, gain, and backlight configuration;
- automatic and manual white-balance configuration;
- optional `duvc_ctl` hardware property control;
- camera warm-up;
- center-crop digital zoom;
- checkerboard-based intrinsic calibration;
- standard pinhole calibration;
- OpenCV fisheye calibration;
- resolution-aware image undistortion;
- cached undistortion maps;
- intrinsic calibration persistence;
- ArUco marker detection;
- marker ID and pixel-corner extraction;
- planar homography calibration;
- pixel-to-physical coordinate transformation;
- homography persistence;
- calibration reports;
- planar reprojection error calculation.

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
webcam_angetube/
├── __init__.py
├── camera.py
├── intrinsic_calibration.py
├── extrinsic_calibration.py
└── aruco_detector.py
```

The package exports:

```text
camera.py
    └── AngetubeCamera

intrinsic_calibration.py
    └── AngetubeIntrinsicCalibration

extrinsic_calibration.py
    └── AngetubeExtrinsicCalibration

aruco_detector.py
    └── AngetubeArucoDetector
```

---

# Component Boundaries

The four public classes deliberately solve different problems.

```text
CAMERA HARDWARE
      │
      ▼
AngetubeCamera
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
AngetubeArucoDetector
        ≠
physical marker layout
```

and:

```text
AngetubeExtrinsicCalibration
        ≠
ArUco detection
```

The detector identifies marker corners in image coordinates.

The extrinsic calibration receives already-established pixel-to-physical point correspondences.

This keeps the camera framework independent of a particular physical calibration setup.

---

# AngetubeCamera

```python
class AngetubeCamera
```

`AngetubeCamera` provides an OpenCV-based acquisition interface with additional camera configuration and hardware-control capabilities.

Its responsibilities include:

```text
open camera
configure stream
configure camera properties
optionally access duvc_ctl
warm up camera
capture frame
apply digital zoom
close camera
```

It does not perform intrinsic calibration, marker detection, extrinsic calibration, segmentation, or measurement.

---

# Constructor

```python
AngetubeCamera(
    camera_index: int,
    width: int | None = None,
    height: int | None = None,
    fps: int | None = None,
    fourcc: str | None = "MJPG",
    backend: int | None = cv2.CAP_DSHOW,
    focus_mode: str | None = None,
    focus_value: int | None = None,
    exposure_mode: str | None = None,
    exposure_value: int | None = None,
    brightness: int | None = None,
    contrast: int | None = None,
    saturation: int | None = None,
    sharpness: int | None = None,
    gain: int | None = None,
    backlight_compensation: int | None = None,
    white_balance_mode: str | None = None,
    white_balance_temperature: int | None = None,
    digital_zoom: float = 1.0,
    warmup_frames: int = 5,
)
```

Example:

```python
from framework.sensing.cameras.webcam_angetube import (
    AngetubeCamera,
)

camera = AngetubeCamera(
    camera_index=1,
    width=3840,
    height=2160,
    fps=30,
    fourcc="MJPG",
    focus_mode="manual",
    focus_value=537,
    digital_zoom=1.0,
)
```

---

# Camera Configuration Attributes

The constructor configuration is retained through public attributes:

```python
camera.camera_index

camera.width
camera.height
camera.fps
camera.fourcc
camera.backend

camera.focus_mode
camera.focus_value

camera.exposure_mode
camera.exposure_value

camera.brightness
camera.contrast
camera.saturation
camera.sharpness
camera.gain
camera.backlight_compensation

camera.white_balance_mode
camera.white_balance_temperature

camera.digital_zoom
camera.warmup_frames
```

These represent requested camera configuration.

Whether a physical webcam accepts a particular hardware property remains dependent on the device, driver, and capture backend.

---

# Camera Index

```python
camera.camera_index
```

The OpenCV camera device index.

It must be an integer.

A non-integer value raises `TypeError`.

---

# Stream Resolution

```python
camera.width
camera.height
```

Optional requested stream dimensions.

If supplied, each value must be greater than zero.

They are requested through:

```text
cv2.CAP_PROP_FRAME_WIDTH
cv2.CAP_PROP_FRAME_HEIGHT
```

when the camera opens.

These values represent requested settings rather than guaranteed hardware output.

The actual stream resolution can be inspected through:

```python
camera.resolution
```

---

# FPS

```python
camera.fps
```

Optional requested frames per second.

When supplied:

```text
fps > 0
```

is required.

The value is requested through:

```text
cv2.CAP_PROP_FPS
```

The camera and backend determine whether the requested FPS can actually be provided.

---

# FOURCC

```python
camera.fourcc
```

Optional four-character video codec identifier.

The default is:

```python
"MJPG"
```

If supplied, the string must contain exactly four characters.

During stream configuration it is converted through:

```python
cv2.VideoWriter_fourcc(...)
```

and requested using:

```text
cv2.CAP_PROP_FOURCC
```

Setting:

```python
fourcc=None
```

skips explicit FOURCC configuration.

---

# Backend

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

the camera is opened using:

```python
cv2.VideoCapture(
    camera_index
)
```

instead of explicitly supplying a backend.

---

# Focus Configuration

The camera supports:

```python
camera.focus_mode
camera.focus_value
```

`focus_mode` may be used as:

```text
auto
manual
```

For OpenCV control:

```text
auto
    │
    ▼
CAP_PROP_AUTOFOCUS = 1

manual
    │
    ▼
CAP_PROP_AUTOFOCUS = 0
    │
    ▼
CAP_PROP_FOCUS = focus_value
```

when a manual focus value is supplied.

The same requested focus configuration is also attempted through the optional `duvc_ctl` controller when available.

---

# Exposure Configuration

The camera supports:

```python
camera.exposure_mode
camera.exposure_value
```

For OpenCV:

```text
auto
    │
    ▼
CAP_PROP_AUTO_EXPOSURE = 0.75

manual
    │
    ▼
CAP_PROP_AUTO_EXPOSURE = 0.25
    │
    ▼
CAP_PROP_EXPOSURE = exposure_value
```

when a manual exposure value is supplied.

The requested exposure configuration is also attempted through `duvc_ctl` when available.

---

# Image Properties

The following optional properties can be requested:

```python
camera.brightness
camera.contrast
camera.saturation
camera.sharpness
camera.gain
camera.backlight_compensation
```

They are applied through corresponding OpenCV capture properties when supplied.

When `duvc_ctl` is available, the implementation also attempts to apply the equivalent hardware properties through the controller.

---

# White Balance

White balance configuration uses:

```python
camera.white_balance_mode
camera.white_balance_temperature
```

The intended modes are:

```text
auto
manual
```

For OpenCV:

```text
auto
    │
    ▼
CAP_PROP_AUTO_WB = 1

manual
    │
    ▼
CAP_PROP_AUTO_WB = 0
    │
    ▼
CAP_PROP_WB_TEMPERATURE
```

when a manual temperature is supplied.

The equivalent control is also attempted through `duvc_ctl` when available.

---

# Optional `duvc_ctl` Hardware Control

The camera module optionally imports:

```python
duvc_ctl
```

If the package is available:

```text
HAS_DUVC = True
```

and `AngetubeCamera` attempts to construct:

```python
duvc.CameraController(
    device_index=camera_index
)
```

before opening the OpenCV stream.

Conceptually:

```text
AngetubeCamera.open()
        │
        ├── attempt duvc_ctl controller
        │       │
        │       └── apply supported hardware properties
        │
        ▼
open OpenCV VideoCapture
        │
        ▼
configure stream
        │
        ▼
apply OpenCV properties
```

The `duvc_ctl` integration is optional.

If the module is not installed, camera acquisition can continue through OpenCV.

If controller creation fails for the selected device, the implementation reports:

```text
[AngetubeCamera] duvc_ctl unavailable for this device: ...
```

and continues without the controller.

This means:

```text
duvc_ctl unavailable
        ≠
camera acquisition unavailable
```

provided OpenCV can still open the camera.

---

# `duvc_ctl` Property Handling

When a `duvc_ctl` controller is available, the implementation attempts to configure:

```text
focus
exposure
brightness
contrast
saturation
sharpness
gain
backlight compensation
white balance
```

For supported numerical properties, the implementation attempts to inspect the controller's property range.

Values below the reported minimum are clamped to the minimum.

Values above the reported maximum are clamped to the maximum.

Unsupported properties or controller-property errors are ignored by the internal hardware-control helpers.

This keeps optional hardware control from becoming a hard requirement for normal camera acquisition.

The underscore-prefixed `duvc_ctl` helpers remain internal implementation details and are not part of the package public API.

---

# Camera State

## `is_open`

```python
camera.is_open -> bool
```

Read-only property indicating whether an active OpenCV capture object exists and reports itself as open.

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

Opens and configures the webcam.

The current sequence is:

```text
open()
  │
  ▼
attempt duvc_ctl controller
  │
  ▼
apply available duvc properties
  │
  ▼
create cv2.VideoCapture
  │
  ▼
verify camera opened
  │
  ▼
configure FOURCC
  │
  ▼
configure width / height / FPS
  │
  ▼
apply OpenCV camera properties
  │
  ▼
warm up camera
```

If the camera is already open, `open()` returns without reopening it.

If OpenCV cannot open the requested camera, the temporary capture is released, the optional controller is closed, and `RuntimeError` is raised.

---

# Actual Camera Resolution

## `resolution`

```python
camera.resolution -> tuple[int, int]
```

Returns the actual current OpenCV stream resolution as:

```text
(width, height)
```

Example:

```python
width, height = camera.resolution
```

This distinguishes:

```text
camera.width / camera.height
        │
        └── requested stream resolution

camera.resolution
        │
        └── actual current stream resolution
```

The camera must be open before accessing this property.

Otherwise `RuntimeError` is raised.

---

# Camera Warm-Up

```python
camera.warmup_frames
```

determines how many frames are read immediately after camera configuration.

The default is:

```python
5
```

The value must not be negative.

During `open()`:

```text
camera configured
       │
       ▼
read warmup frame
       │
       ▼
read warmup frame
       │
       ▼
...
       │
       ▼
camera ready for capture()
```

Warm-up frames are discarded.

This gives the camera and automatic controls an opportunity to stabilize before the first application frame is returned.

Setting:

```python
warmup_frames=0
```

disables this warm-up sequence.

---

# Capturing a Frame

## `capture()`

```python
camera.capture() -> numpy.ndarray
```

Captures one frame from the webcam.

Example:

```python
frame = camera.capture()
```

The process is:

```text
OpenCV capture
      │
      ▼
raw frame
      │
      ▼
digital zoom if configured
      │
      ▼
returned frame
```

The camera must already be open.

If it is not open, `RuntimeError` is raised.

If OpenCV fails to acquire a valid frame, `RuntimeError` is also raised.

---

# Digital Zoom

```python
camera.digital_zoom
```

controls software-based center zoom.

The value must satisfy:

```text
digital_zoom >= 1.0
```

A value of:

```python
1.0
```

means effectively no digital zoom.

For zoom values greater than approximately `1.0`, the implementation:

```text
captured frame
      │
      ▼
calculate smaller center crop
      │
      ▼
crop around image center
      │
      ▼
resize crop back to
original frame dimensions
      │
      ▼
returned image
```

Therefore the output image retains the original captured pixel dimensions.

Conceptually:

```text
original frame
┌─────────────────────────┐
│                         │
│     ┌─────────────┐     │
│     │ center crop │     │
│     └─────────────┘     │
│                         │
└─────────────────────────┘
             │
             ▼
       resize to original
          resolution
```

This is **digital image zoom**, not an optical camera zoom.

It changes the image content used by later calibration and sensing operations.

---

# Closing the Camera

## `close()`

```python
camera.close() -> None
```

Releases both camera-control resources:

```text
OpenCV capture
      +
optional duvc_ctl controller
```

After closing:

```python
camera.is_open == False
```

Calling `close()` when no capture or controller exists is safe.

---

# Basic Acquisition Example

```python
from framework.sensing.cameras.webcam_angetube import (
    AngetubeCamera,
)

camera = AngetubeCamera(
    camera_index=1,
    width=3840,
    height=2160,
    fourcc="MJPG",
    focus_mode="manual",
    focus_value=537,
    digital_zoom=1.0,
)

camera.open()

try:
    print(
        camera.resolution
    )

    frame = camera.capture()

finally:
    camera.close()
```

---

# AngetubeIntrinsicCalibration

```python
class AngetubeIntrinsicCalibration
```

`AngetubeIntrinsicCalibration` performs checkerboard-based intrinsic camera calibration.

Unlike the current Arducam intrinsic implementation, the Angetube implementation supports two calibration models:

```text
standard
    │
    └── OpenCV pinhole calibration

fisheye
    │
    └── OpenCV fisheye calibration
```

The default is:

```python
calibration_model="fisheye"
```

This reflects the wide-angle webcam configuration while retaining standard pinhole calibration as an alternative.

---

# Intrinsic Constructor

```python
AngetubeIntrinsicCalibration(
    checkerboard_inner_corners: tuple[int, int],
    square_size_mm: float,
    calibration_model: str = "fisheye",
    fisheye_balance: float = 0.0,
    fisheye_fov_scale: float = 1.0,
    fisheye_check_cond: bool = True,
    fisheye_recompute_extrinsic: bool = True,
    fisheye_fix_skew: bool = True,
)
```

Example:

```python
from framework.sensing.cameras.webcam_angetube import (
    AngetubeIntrinsicCalibration,
)

calibration = AngetubeIntrinsicCalibration(
    checkerboard_inner_corners=(9, 6),
    square_size_mm=25.0,
    calibration_model="fisheye",
)
```

---

# Calibration Model

```python
calibration.calibration_model
```

is normalized to lowercase and must be either:

```text
standard
fisheye
```

Any other value raises `ValueError`.

---

# `is_fisheye`

```python
calibration.is_fisheye -> bool
```

Returns:

```python
True
```

when:

```python
calibration.calibration_model == "fisheye"
```

and otherwise returns `False`.

---

# Checkerboard Configuration

```python
calibration.checkerboard_inner_corners
calibration.square_size_mm
```

`checkerboard_inner_corners` stores:

```text
(columns, rows)
```

of checkerboard inner corners.

Both values must be positive.

`square_size_mm` represents the physical checkerboard square size in millimetres and must also be greater than zero.

---

# Fisheye Configuration

The fisheye model exposes:

```python
calibration.fisheye_balance
calibration.fisheye_fov_scale

calibration.fisheye_check_cond
calibration.fisheye_recompute_extrinsic
calibration.fisheye_fix_skew
```

---

## `fisheye_balance`

```text
0.0 <= fisheye_balance <= 1.0
```

The default is:

```python
0.0
```

It is used when calculating the new camera matrix for fisheye undistortion.

Values outside the accepted range raise `ValueError`.

---

## `fisheye_fov_scale`

The default is:

```python
1.0
```

and the value must be greater than zero.

It is passed to OpenCV's fisheye new-camera-matrix estimation during undistortion.

---

## Fisheye Calibration Flags

The following configuration controls OpenCV fisheye calibration flags:

```python
fisheye_check_cond
fisheye_recompute_extrinsic
fisheye_fix_skew
```

Their defaults are all:

```python
True
```

They correspond to:

```text
CALIB_CHECK_COND
CALIB_RECOMPUTE_EXTRINSIC
CALIB_FIX_SKEW
```

The implementation obtains these flags from `cv2.fisheye` when available and uses numeric fallback values for compatibility.

---

# Intrinsic Calibration Results

The following public state is available:

```python
calibration.camera_matrix
calibration.dist_coeffs
calibration.image_size
calibration.rms_error

calibration.accepted_images
calibration.total_images
```

Before calibration:

```text
camera_matrix = None
dist_coeffs = None
image_size = None
rms_error = None

accepted_images = 0
total_images = 0
```

After successful calibration they contain the computed camera model and calibration statistics.

---

# Intrinsic Calibration State

## `is_calibrated`

```python
calibration.is_calibrated -> bool
```

Returns `True` only when:

```text
camera_matrix
dist_coeffs
image_size
rms_error
```

are all available.

A calibration loaded from disk is also considered calibrated.

---

# Performing Intrinsic Calibration

## `calibrate()`

```python
calibration.calibrate(
    image_paths: Iterable[str | Path],
) -> None
```

The overall process is:

```text
calibration images
       │
       ▼
read image
       │
       ▼
convert to grayscale
       │
       ▼
detect checkerboard
       │
       ▼
refine corners
       │
       ├──────────────────────┐
       │                      │
       ▼                      ▼
standard model          fisheye model
       │                      │
       ▼                      ▼
cv2.calibrateCamera     cv2.fisheye.calibrate
       │                      │
       └──────────┬───────────┘
                  ▼
        camera matrix + distortion
                  │
                  ▼
             RMS error
```

---

# Checkerboard Detection

The current checkerboard detector uses:

```python
cv2.findChessboardCorners(...)
```

with:

```text
CALIB_CB_ADAPTIVE_THRESH
CALIB_CB_FAST_CHECK
CALIB_CB_NORMALIZE_IMAGE
```

Detected corners are refined using:

```python
cv2.cornerSubPix(...)
```

Images that cannot be read are skipped.

Images where the checkerboard is not found are also skipped.

---

# Image Acceptance

The calibration object records:

```python
calibration.total_images
calibration.accepted_images
```

where:

```text
total_images
    │
    └── number of supplied image paths

accepted_images
    │
    └── number where checkerboard detection succeeded
```

If no images are supplied, `ValueError` is raised.

If the checkerboard cannot be detected in any supplied readable image, `RuntimeError` is raised.

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

---

# Standard Pinhole Calibration

When:

```python
calibration_model="standard"
```

the implementation uses:

```python
cv2.calibrateCamera(...)
```

The camera matrix has the conventional form:

```text
      [ fx   0   cx ]
K  =  [  0  fy   cy ]
      [  0   0    1 ]
```

and OpenCV estimates the standard distortion coefficients.

---

# Fisheye Calibration

When:

```python
calibration_model="fisheye"
```

the implementation uses:

```python
cv2.fisheye.calibrate(...)
```

with:

```text
4 × 1 distortion coefficient vector
```

and the configured fisheye calibration flags.

Conceptually:

```text
checkerboard observations
        │
        ▼
cv2.fisheye.calibrate
        │
        ├── K
        └── D
```

---

# Fisheye `CHECK_COND` Retry

The current implementation includes a compatibility/fallback behavior for fisheye calibration.

It first attempts calibration using the configured flags.

If OpenCV raises `cv2.error` and:

```python
fisheye_check_cond == True
```

the implementation removes:

```text
CALIB_CHECK_COND
```

and retries the calibration.

Conceptually:

```text
fisheye calibration
      │
      ▼
CHECK_COND enabled
      │
      ├── success → use result
      │
      └── cv2.error
             │
             ▼
        remove CHECK_COND
             │
             ▼
          retry once
```

If `fisheye_check_cond` was already disabled, the OpenCV error is re-raised.

---

# Undistortion

## `undistort()`

```python
calibration.undistort(
    image: numpy.ndarray,
) -> numpy.ndarray
```

Returns an undistorted image using the currently loaded calibration model.

Example:

```python
undistorted = calibration.undistort(
    frame
)
```

The input must be a grayscale or BGR image.

Passing `None` or an unsupported image dimensionality raises `ValueError`.

A calibration must already exist.

Otherwise `RuntimeError` is raised.

---

# Model-Specific Undistortion

The undistortion implementation follows different OpenCV paths depending on the calibration model.

For fisheye:

```text
scaled camera matrix
       │
       ▼
estimateNewCameraMatrixForUndistortRectify
       │
       ▼
fisheye.initUndistortRectifyMap
       │
       ▼
cv2.remap
```

For standard calibration:

```text
scaled camera matrix
       │
       ▼
cv2.getOptimalNewCameraMatrix
       │
       ▼
cv2.initUndistortRectifyMap
       │
       ▼
cv2.remap
```

This allows the public:

```python
undistort()
```

interface to remain the same for both models.

---

# Resolution-Aware Undistortion

The calibration stores the image size used during calibration.

When undistorting another resolution, the implementation scales the stored camera matrix for the requested image size before creating the undistortion maps.

Conceptually:

```text
calibration resolution
       │
       ▼
stored camera matrix
       │
       ▼
current image resolution
       │
       ▼
scaled camera matrix
       │
       ▼
undistortion maps
```

This allows the calibration to account for different image dimensions without directly reusing unscaled pixel-space intrinsic parameters.

---

# Cached Undistortion Maps

Undistortion maps are cached internally.

The cache key includes:

```text
image width
image height
calibration model
fisheye balance
fisheye FOV scale
```

Conceptually:

```text
undistort image
      │
      ▼
maps already cached?
      │
   ┌──┴──┐
  YES    NO
   │      │
   │      ▼
   │   calculate maps
   │      │
   │      ▼
   │   cache maps
   │      │
   └──────┴──────► cv2.remap
```

This avoids rebuilding the same undistortion maps for every captured frame.

The cache itself is an internal implementation detail.

It is cleared when a new calibration is computed or loaded.

---

# Saving Intrinsic Calibration

## `save()`

```python
calibration.save(
    file_path: str | Path,
) -> None
```

Saves machine-readable calibration data to an NPZ file.

The stored data include:

```text
camera_matrix
dist_coeffs
image_size
rms_error

accepted_images
total_images

calibration_model
is_fisheye

fisheye_balance
fisheye_fov_scale
fisheye_check_cond
fisheye_recompute_extrinsic
fisheye_fix_skew

checkerboard_inner_corners
square_size_mm
```

Parent directories are created automatically.

A valid calibration must exist before saving.

---

# Intrinsic Text Report

## `save_text_report()`

```python
calibration.save_text_report(
    file_path: str | Path,
) -> None
```

Writes a human-readable calibration report.

The report includes:

```text
calibration model
checkerboard inner corners
checkerboard square size
accepted images
total images
image resolution
RMS reprojection error
camera matrix
distortion coefficients
```

For fisheye calibration it additionally includes:

```text
fisheye balance
fisheye FOV scale
CHECK_COND configuration
RECOMPUTE_EXTRINSIC configuration
FIX_SKEW configuration
```

The report labels the selected model as either:

```text
OpenCV Fisheye
```

or:

```text
Standard Pinhole
```

---

# Loading Intrinsic Calibration

## `load()`

```python
AngetubeIntrinsicCalibration.load(
    file_path: str | Path,
) -> AngetubeIntrinsicCalibration
```

Loads a saved NPZ calibration.

Example:

```python
calibration = (
    AngetubeIntrinsicCalibration.load(
        "calibration/camera_intrinsics.npz"
    )
)
```

The loader reconstructs:

```text
calibration model
checkerboard configuration
square size
fisheye configuration
camera matrix
distortion coefficients
image size
RMS error
accepted image count
total image count
```

The loader also contains compatibility fallbacks for calibration files where some newer configuration fields are absent.

If the calibration file does not exist, `FileNotFoundError` is raised.

---

# Intrinsic Calibration Example

```python
from pathlib import Path

from framework.sensing.cameras.webcam_angetube import (
    AngetubeIntrinsicCalibration,
)

calibration = AngetubeIntrinsicCalibration(
    checkerboard_inner_corners=(9, 6),
    square_size_mm=25.0,
    calibration_model="fisheye",
)

images = sorted(
    Path(
        "calibration/images"
    ).glob(
        "*.jpg"
    )
)

calibration.calibrate(
    images
)

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

# AngetubeArucoDetector

```python
class AngetubeArucoDetector
```

`AngetubeArucoDetector` detects ArUco markers in an image.

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
AngetubeArucoDetector(
    dictionary_name: str,
)
```

Example:

```python
from framework.sensing.cameras.webcam_angetube import (
    AngetubeArucoDetector,
)

detector = AngetubeArucoDetector(
    dictionary_name="DICT_4X4_50",
)
```

`dictionary_name` must correspond to an ArUco dictionary exposed by:

```python
cv2.aruco
```

A non-string value raises `TypeError`.

An unknown dictionary name raises `ValueError`.

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
    └── configured dictionary name

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

The input may be:

```text
BGR image
or
grayscale image
```

BGR input is converted internally to grayscale.

A grayscale image is used directly.

Passing `None` or an unsupported image dimensionality raises `ValueError`.

---

# Detection Result

The result is:

```python
{
    marker_id: corners,
}
```

Each corner array contains four image-space marker corners:

```text
shape = (4, 2)
dtype = float32
```

Conceptually:

```python
{
    10: [
        [x0, y0],
        [x1, y1],
        [x2, y2],
        [x3, y3],
    ]
}
```

If no markers are detected:

```python
{}
```

is returned.

---

# Marker Detection Boundary

The detector answers:

```text
Which marker IDs are visible?

Where are their corners in the image?
```

It does not answer:

```text
Where is the marker physically located?

What physical coordinate belongs to this corner?

Which marker defines the origin?

How large is the physical workspace?
```

Those relationships remain application-specific.

---

# AngetubeExtrinsicCalibration

```python
class AngetubeExtrinsicCalibration
```

`AngetubeExtrinsicCalibration` provides planar homography-based calibration.

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

---

# Extrinsic Constructor

```python
AngetubeExtrinsicCalibration()
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

Returns `True` when a homography exists.

---

# Computing the Homography

## `calibrate()`

```python
calibration.calibrate(
    pixel_points,
    world_points_mm,
)
```

Both inputs must have shape:

```text
(N, 2)
```

They must contain the same number of points and at least four correspondences.

The current implementation uses:

```python
cv2.findHomography(
    pixel_points,
    world_points_mm,
    method=0,
)
```

Therefore the mapping is calculated directly without a robust RANSAC method.

If OpenCV cannot calculate the homography, `RuntimeError` is raised.

---

# Reprojection Errors

After calibration:

```python
calibration.reprojection_errors_mm
```

contains the Euclidean physical-space reprojection error for each supplied calibration point.

Conceptually:

```text
pixel calibration point
       │
       ▼
homography
       │
       ▼
predicted physical point
       │
       ▼
compare with supplied physical point
       │
       ▼
error in millimetres
```

---

# Transforming Pixel Coordinates

## `transform_points()`

```python
calibration.transform_points(
    pixel_points,
)
```

Transforms points with shape:

```text
(N, 2)
```

from image coordinates into:

```text
(x_mm, y_mm)
```

using:

```python
cv2.perspectiveTransform(...)
```

A homography must already exist.

Otherwise `RuntimeError` is raised.

---

# Physical Coordinate System

The extrinsic class does not define the physical coordinate frame.

The supplied:

```python
world_points_mm
```

define:

```text
origin
axis directions
scale
physical dimensions
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

defines a rectangular planar coordinate system in millimetres.

The application decides which detected image points correspond to those physical positions.

---

# Saving Extrinsic Calibration

## `save()`

```python
calibration.save(
    file_path,
) -> None
```

Stores:

```text
homography
```

in an NPZ file.

Parent directories are created automatically.

A valid calibration must exist before saving.

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

Writes a human-readable report containing:

```text
homography matrix
```

and, when supplied:

```text
pixel calibration points
world calibration points
```

If reprojection errors are available, the report also contains the error for each calibration point in millimetres.

---

# Loading Extrinsic Calibration

## `load()`

```python
AngetubeExtrinsicCalibration.load(
    file_path,
)
```

Loads a saved homography.

The loaded instance receives:

```python
calibration.homography
```

and is therefore considered calibrated.

The saved NPZ currently contains only the homography.

`reprojection_errors_mm` are not reconstructed when loading.

---

# Combining ArUco Detection and Planar Calibration

The detector and extrinsic calibration can be combined, but the physical correspondence is supplied by the application.

```text
undistorted image
       │
       ▼
AngetubeArucoDetector
       │
       ▼
marker IDs + pixel corners
       │
       ▼
application-specific physical layout
       │
       ▼
pixel_points + world_points_mm
       │
       ▼
AngetubeExtrinsicCalibration
       │
       ▼
homography
```

This boundary keeps the generic camera package independent of a particular calibration-board or workspace-marker arrangement.

---

# Intrinsic and Extrinsic Calibration

The two calibration classes solve different geometric problems.

```text
INTRINSIC

checkerboard images
       │
       ▼
camera model
       │
       ├── K
       └── distortion
       │
       ▼
undistorted image
```

versus:

```text
PLANAR EXTRINSIC

pixel coordinates
       +
physical coordinates
       │
       ▼
homography
       │
       ▼
pixel → millimetre mapping
```

The current Angetube intrinsic model may itself be either:

```text
standard pinhole
        or
OpenCV fisheye
```

while the extrinsic model remains a planar homography in both cases.

---

# Digital Zoom and Calibration

Digital zoom is applied by `AngetubeCamera.capture()` after the physical camera frame is acquired.

Therefore:

```text
camera frame
      │
      ▼
center crop
      │
      ▼
resize
      │
      ▼
returned image
```

changes the pixel geometry seen by downstream processing.

Conceptually:

```text
physical camera configuration
        +
digital zoom configuration
        │
        ▼
effective image geometry
        │
        ▼
calibration / sensing
```

Calibration and later sensing should therefore use image geometry that is consistent with the acquisition configuration expected by the application.

The camera framework does not automatically modify an existing calibration when `digital_zoom` changes.

---

# Camera Properties and Calibration Stability

Properties such as:

```text
focus
exposure
white balance
digital zoom
stream resolution
```

belong to camera acquisition rather than intrinsic calibration itself.

However, they determine the images supplied to calibration and later sensing.

The framework deliberately keeps:

```text
camera configuration
        │
        ▼
AngetubeCamera
```

separate from:

```text
geometric calibration
        │
        ▼
AngetubeIntrinsicCalibration
```

Higher-level applications are responsible for using a consistent camera configuration when calibration consistency is required.

---

# Complete Usage Flow

A higher-level application can combine the package components as follows:

```text
1. Configure camera
       │
       ▼
2. Open camera
       │
       ├── optional duvc_ctl
       ├── stream configuration
       ├── OpenCV properties
       └── warm-up
       │
       ▼
3. Capture frame
       │
       ▼
4. Apply configured digital zoom
       │
       ▼
5. Apply intrinsic undistortion
       │
       ▼
6. Detect ArUco markers
       │
       ▼
7. Application resolves physical
   marker correspondences
       │
       ▼
8. Compute/load planar homography
       │
       ▼
9. Transform relevant image points
   into physical millimetres
       │
       ▼
10. Higher-level sensing operation
    interprets the result
```

Example:

```python
from framework.sensing.cameras.webcam_angetube import (
    AngetubeCamera,
    AngetubeIntrinsicCalibration,
    AngetubeExtrinsicCalibration,
    AngetubeArucoDetector,
)

camera = AngetubeCamera(
    camera_index=1,
    width=3840,
    height=2160,
    fourcc="MJPG",
    focus_mode="manual",
    focus_value=537,
)

intrinsics = (
    AngetubeIntrinsicCalibration.load(
        "calibration/camera_intrinsics.npz"
    )
)

extrinsics = (
    AngetubeExtrinsicCalibration.load(
        "calibration/camera_extrinsics.npz"
    )
)

detector = AngetubeArucoDetector(
    dictionary_name="DICT_4X4_50",
)

camera.open()

try:
    frame = camera.capture()

    undistorted = (
        intrinsics.undistort(
            frame
        )
    )

    markers = detector.detect(
        undistorted
    )

    # Higher-level application logic
    # determines how detected marker
    # points relate to physical references.

finally:
    camera.close()
```

---

# Calibration Persistence

The package separates machine-readable calibration data from human-readable reports.

```text
MACHINE-READABLE

intrinsic .npz
    │
    ├── calibration model
    ├── camera matrix
    ├── distortion coefficients
    ├── image size
    ├── RMS error
    ├── checkerboard configuration
    └── fisheye configuration

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

Maintaining this distinction is important when combining intrinsic and planar calibration.

---

# Error and Validation Behavior

Typical public-facing errors include:

| Condition | Error |
|---|---|
| Non-integer camera index | `TypeError` |
| Non-positive requested width/height | `ValueError` |
| Non-positive requested FPS | `ValueError` |
| FOURCC not exactly four characters | `ValueError` |
| Digital zoom below `1.0` | `ValueError` |
| Negative warm-up frame count | `ValueError` |
| Camera cannot open | `RuntimeError` |
| Capture requested while camera is closed | `RuntimeError` |
| Frame acquisition fails | `RuntimeError` |
| Invalid checkerboard dimensions | `ValueError` |
| Non-positive checkerboard square size | `ValueError` |
| Unknown calibration model | `ValueError` |
| Fisheye balance outside `0.0–1.0` | `ValueError` |
| Non-positive fisheye FOV scale | `ValueError` |
| No intrinsic calibration images | `ValueError` |
| Mixed readable calibration image resolutions | `ValueError` |
| Checkerboard detected in no images | `RuntimeError` |
| Intrinsic operation without calibration | `RuntimeError` |
| Invalid image passed to undistortion | `ValueError` |
| Missing calibration file | `FileNotFoundError` |
| Unknown ArUco dictionary | `ValueError` |
| Invalid detector image | `ValueError` |
| Invalid homography point shape | `ValueError` |
| Unequal correspondence counts | `ValueError` |
| Fewer than four planar correspondences | `ValueError` |
| Homography cannot be computed | `RuntimeError` |
| Extrinsic operation before calibration | `RuntimeError` |

Optional `duvc_ctl` property failures are generally handled internally rather than exposed as hard acquisition failures.

---

# Relationship to Higher-Level Sensing

This package provides camera-level capabilities.

A higher-level sensing operation may build on it:

```text
CAMERA FRAMEWORK

camera acquisition
camera property control
intrinsic calibration
ArUco detection
planar calibration
        │
        ▼
APPLICATION SENSING

workspace selection
session / entry selection
object segmentation
measurement
object identity
artifact generation
persistence
```

The Angetube package should therefore remain independent of:

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

# Relationship to Other Camera Implementations

The Angetube package follows the same general responsibility separation as other camera packages:

```text
camera acquisition
       │
intrinsic calibration
       │
marker detection
       │
planar extrinsic calibration
```

but its implementation remains camera-specific.

In particular, the Angetube implementation currently includes capabilities such as:

```text
extended stream configuration
camera property control
optional duvc_ctl integration
digital zoom
standard + fisheye intrinsic models
resolution-aware undistortion
cached undistortion maps
```

These should not be assumed to exist identically in another camera implementation.

Higher-level camera abstractions should therefore depend only on capabilities they deliberately define as shared rather than assuming implementation equivalence between camera packages.

---

# Public API

The supported package-level imports are:

```python
from framework.sensing.cameras.webcam_angetube import (
    AngetubeCamera,
    AngetubeIntrinsicCalibration,
    AngetubeExtrinsicCalibration,
    AngetubeArucoDetector,
)
```

| Public object | Responsibility |
|---|---|
| `AngetubeCamera` | Configure, open, control, capture from, digitally zoom, and close the webcam. |
| `AngetubeIntrinsicCalibration` | Compute, persist, load, and apply standard or fisheye intrinsic calibration. |
| `AngetubeExtrinsicCalibration` | Compute, persist, load, and apply planar pixel-to-physical homography calibration. |
| `AngetubeArucoDetector` | Detect ArUco marker IDs and image-space marker corners. |

Internal implementation details and underscore-prefixed helpers are not part of the public API.

In particular, internal helpers for:

```text
stream configuration
OpenCV property application
duvc_ctl control
property clamping
digital zoom
camera warm-up
calibration point preparation
fisheye calibration
undistortion-map generation
camera-matrix scaling
point validation
```

are implementation details rather than public framework contracts.

---

# Summary

The Angetube webcam package establishes four reusable public capabilities:

```text
AngetubeCamera
      │
      ├── stream configuration
      ├── hardware/property control
      └── acquisition
      │
      ▼
camera image

AngetubeIntrinsicCalibration
      │
      ├── standard pinhole
      └── fisheye
      │
      ▼
calibrated image geometry

AngetubeArucoDetector
      │
      ▼
marker IDs + pixel corners

AngetubeExtrinsicCalibration
      │
      ▼
planar physical coordinates
```

Their responsibilities remain deliberately separate:

```text
camera acquisition / control
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

The package therefore provides reusable webcam acquisition and calibration primitives while leaving physical setup interpretation, sensing semantics, persistence, and distributed execution to higher-level components.