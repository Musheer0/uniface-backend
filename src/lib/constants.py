"""Shared constants for the Blurfield backend."""

import os

base_api_path = "/api"

# ---------------------------------------------------------------------------
# Face matching
# ---------------------------------------------------------------------------
# `compute_similarity(..., normalized=True)` returns a *distance-like* score:
# lower  => same person, higher => different person.
# Filtered routes keep the reference face clear and blur every detected face
# whose distance to the reference embedding is <= threshold... actually the
# current convention is inverted on purpose:
#   distance <= SIMILARITY_THRESHOLD  ->  face is *different* -> blur it
#   distance  > SIMILARITY_THRESHOLD  ->  face matches reference -> keep clear
# A single shared threshold keeps photo / video / timestamp paths consistent.
SIMILARITY_THRESHOLD = 0.3

# ---------------------------------------------------------------------------
# Video / timestamp limits
# ---------------------------------------------------------------------------
MAX_TIMESTAMP_RANGES = 32
MAX_TIMESTAMP_SECONDS = 6 * 60 * 60  # 6h — sanity cap for a single range bound
MAX_VIDEO_SECONDS = 60 * 60  # 1h — processed videos longer than this are rejected
MAX_VIDEO_PIXELS = 3840 * 2160  # 4K — wider/taller frames are rejected

# Response header names used by TrackingHeadersMiddleware (see middlewares).
HEADER_USER_ID = "X-User-Id"
HEADER_GENERATION_ID = "X-Generation-Id"

# ---------------------------------------------------------------------------
# Temp working dirs (single source of truth — src.main re-exports these).
# Overridable via TEMP_DIR env var; absolute paths recommended on Modal.
# ---------------------------------------------------------------------------
TEMP_DIR = os.getenv("TEMP_DIR", "temp")

OUTPUT_VIDEOS_DIR = os.path.join(TEMP_DIR, "outputs", "videos")
OUTPUT_IMAGES_DIR = os.path.join(TEMP_DIR, "outputs", "images")

INPUT_VIDEOS_DIR = os.path.join(TEMP_DIR, "inputs", "videos")
INPUT_IMAGES_DIR = os.path.join(TEMP_DIR, "inputs", "images")
