# Uniface — Backend

GPU-backed face-blurring API for photos and videos. Built with **FastAPI**, deployed on **Modal** (CUDA image), using **UniFace** (`RetinaFace` detection + `ArcFace` recognition + `BlurFace` anonymization) with **S3-compatible object storage** for input/output files.

## How it works

1. Client uploads source media to S3 and calls the API with S3 keys.
2. API downloads the file to `temp/inputs/<type>/<generation_id>/...` (per-request subdir, so concurrent jobs sharing keys don't collide).
3. Every face is detected (photo: whole image; video: frame-by-frame with OpenCV). For `filtered` routes, the reference face (`face_key`) is embedded with ArcFace and only **non-matching** faces are blurred (distance `<= SIMILARITY_THRESHOLD`); the matching person stays clear.
4. Blurred result is written to `temp/outputs/...` and uploaded to S3 at `output_key`.
5. Temp input + reference files are always deleted (`try/finally`); the output temp file is deleted after upload (or on failure).

## Tech stack

| Layer | Choice |
|---|---|
| API | FastAPI + Uvicorn |
| Hosting | Modal (`modal.App("blurfield-api")`, `@modal.asgi_app()`, 30-min function timeout) |
| Image | `nvidia/cuda:13.3.0-cudnn-devel-ubuntu24.04`, Python 3.12, `ffmpeg`, `requirements.txt` |
| Face detection | `uniface.detection.RetinaFace` (process-cached, warmed via `/readyz`) |
| Face recognition | `uniface.recognition.ArcFace` (process-cached; reference embeddings cached by content hash) |
| Blurring | `uniface.privacy.BlurFace` |
| Video I/O | OpenCV (`VideoCapture` / `VideoWriter` mp4v) + shared `ffmpeg` remux helper (`src/lib/ffmpeg.py`: libx264 + AAC, audio copied from source) |
| Storage | `boto3` S3 client with `AWS_ENDPOINT_URL_S3` + `AWS_REGION` support |
| Auth | API-key header (`x-api-key`, legacy `api-key` accepted) vs `API_KEY`, constant-time compare |
| Tracking | `TrackingHeadersMiddleware` echoes `user_id`/`generation_id` from JSON body as `X-User-Id` / `X-Generation-Id` response headers |
| Validation | Pydantic schemas (`S3Key` traversal guard, timestamp-range checks) |
| Observability | Structured logging with `generation_id`, `/healthz` + `/readyz`, optional Sentry via `SENTRY_DSN` |

## Project structure

```
backend/
├── src/
│   ├── main.py                          # Modal app + image + create_app() (health, tracking, Sentry, timeout)
│   ├── routers/
│   │   ├── photo_routers.py             # POST /api/blur-photo/...
│   │   ├── video_routers.py             # POST /api/blur-video/... (+ legacy /filerer alias)
│   │   ├── video_timestamp_routers.py   # POST /api/blur-video-timestamp/... (+ alias)
│   │   ├── health_routers.py            # GET /healthz, /readyz (no auth)
│   │   └── _helpers.py                  # error mapping + temp cleanup
│   ├── schemas/
│   │   ├── base_schema.py               # BaseRequest { user_id, generation_id }
│   │   ├── common.py                    # S3Key (traversal-safe)
│   │   ├── blur_photo_schemas.py        # img_key, blur_method, output_key [+ face_key]
│   │   ├── blur_video_schemas.py        # video_key, blur_method, output_key [+ face_key]
│   │   └── blur_video_timestamp_schemas.py  # ... + timestamp_ranges (validated)
│   ├── types/
│   │   ├── blur_types.py                # BlurMethod enum + TimestampRange(s)
│   │   └── base_response.py             # BaseResponse { success, generation_id?, user_id?, message?, error? }
│   ├── middlewares/
│   │   └── auth_middleware.py           # InternalAuthorization + TrackingHeadersMiddleware
│   └── lib/
│       ├── blur_image.py                # blur_image, blur_image_with_filter
│       ├── blur_video.py                # blur_video, blur_video_filtered (+ _open_capture caps)
│       ├── blur_video_with_timestamps.py# timestamp-gated variants (+ validate_timestamps)
│       ├── ffmpeg.py                    # single shared ffmpeg remux builder
│       ├── paths.py                     # safe_join / ensure_parent sandbox helpers
│       ├── constants.py                 # base path, SIMILARITY_THRESHOLD, caps, header names, temp dirs
│       ├── get_detector.py              # lru-cached RetinaFace / ArcFace + warmup()
│       ├── get_single_face_embedding.py # reference embedding + SHA-256 cache
│       ├── computer_similarity.py       # typed uniface.compute_similarity wrapper
│       └── download_file.py / upload_file.py / s3.py  # S3 helpers (endpoint-aware)
├── test/                                # pytest suite (30 tests, no GPU/S3 needed)
├── requirements.txt                     # runtime (Modal image)
├── requirements-dev.txt                 # dev/test only (pytest, httpx, ruff, mypy)
├── pyproject.toml                       # pytest/ruff/mypy config
├── test.py                              # local webcam demo (manual, unchanged)
└── .env                                 # NOT committed — env var names below
```

Temp layout (base overridable via `TEMP_DIR`):

```
temp/inputs/videos/<generation_id>/...   temp/inputs/images/<generation_id>/...
temp/outputs/videos/<generation_id>/...  temp/outputs/images/<generation_id>/...
```

## API reference

Base path: `/api`. All blur routes require the API-key header (see Auth). Success responses echo the tracking IDs:

```json
{ "success": true, "generation_id": "g_123", "user_id": "u_123" }
```

Errors use standard HTTP codes: `400` bad media/keys/ranges, `401` auth, `404` missing S3 key, `422` no face in reference image, `500` server/encoding faults. Every response also carries `X-User-Id` / `X-Generation-Id` headers when the request body contained them.

### Blur methods

`BlurMethod`: `pixelate` | `gaussian` | `blackout` | `elliptical` | `median`

### 1. Photos — `/api/blur-photo`

**POST `/api/blur-photo/everyone`** — blur all faces.

```json
{
  "user_id": "u_123",
  "generation_id": "g_123",
  "img_key": "inputs/photo.jpg",
  "blur_method": "pixelate",
  "output_key": "outputs/photo_blurred.jpg"
}
```

**POST `/api/blur-photo/everyone/filtered`** — blur everyone *except* the reference face.

```json
{
  "user_id": "u_123",
  "generation_id": "g_123",
  "img_key": "inputs/group.jpg",
  "face_key": "inputs/me.jpg",
  "blur_method": "gaussian",
  "output_key": "outputs/group_blurred.jpg"
}
```

### 2. Videos — `/api/blur-video`

**POST `/api/blur-video/everyone`**

```json
{
  "user_id": "u_123",
  "generation_id": "g_123",
  "video_key": "inputs/clip.mp4",
  "blur_method": "pixelate",
  "output_key": "outputs/clip_blurred.mp4"
}
```

**POST `/api/blur-video/everyone/filtered`** — filtered variant (`/everyone/filerer` kept as a hidden legacy alias for the old typo).

### 3. Timestamped videos — `/api/blur-video-timestamp`

Only frames whose timestamp in **seconds** (`frame_number / fps`, inclusive `start <= t <= end`) falls inside any `[start, end]` range are blurred; other frames pass through. Max 32 ranges, each end ≤ 6h. Audio is copied from the original.

**POST `/api/blur-video-timestamp/everyone`**

```json
{
  "user_id": "u_123",
  "generation_id": "g_123",
  "video_key": "inputs/clip.mp4",
  "blur_method": "blackout",
  "output_key": "outputs/clip_partial.mp4",
  "timestamp_ranges": [[2.5, 6.0], [12.0, 15.5]]
}
```

**POST `/api/blur-video-timestamp/everyone/filtered`** — filtered + timestamped (adds `face_key`; same legacy alias).

### Ops — no auth

- `GET /healthz` → `{ "ok": true }`
- `GET /readyz` → warms cached models, reports onnxruntime providers + S3 reachability + temp dir.

### Auth

`InternalAuthorization` accepts the canonical `x-api-key` header (legacy `api-key` still works), compares with `API_KEY` using `secrets.compare_digest`, `401` on missing/invalid, `500` if the server has no `API_KEY` configured.

```bash
curl -X POST "$BASE_URL/api/blur-photo/everyone" \
  -H "Content-Type: application/json" \
  -H "x-api-key: $API_KEY" \
  -d '{"user_id":"u1","generation_id":"g1","img_key":"inputs/a.jpg","blur_method":"pixelate","output_key":"outputs/a.jpg"}'
```

## Environment variables

Never commit real values (`.env` is gitignored). Required names:

| Var | Used by |
|---|---|
| `API_KEY` | auth middleware (fatal 500 if unset) |
| `S3_BUCKET` | `src/lib/s3.py` (fatal if unset at request time) |
| `AWS_ENDPOINT_URL_S3` | S3-compatible endpoint (e.g. Neon storage) |
| `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` | S3 auth (via boto3 default chain) |
| `AWS_REGION` | S3 region |
| `MODAL_SECRET_NAME` | Modal secret name (default `blur`) |
| `MODAL_TIMEOUT_SECONDS` | Modal function timeout (default `1800`) |
| `TEMP_DIR` | temp base dir (default `temp`) |
| `LOG_LEVEL` | log level (default `INFO`) |
| `SENTRY_DSN` / `SENTRY_ENV` | optional Sentry |
| `DATABASE_URL` / `DATABASE_URL_POOLED` | present in `.env`, still unused (no DB layer yet) |

## Run & deploy

```bash
# Modal secret (name overridable via MODAL_SECRET_NAME)
modal secret create blur API_KEY=... S3_BUCKET=... AWS_ENDPOINT_URL_S3=... \
  AWS_ACCESS_KEY_ID=... AWS_SECRET_ACCESS_KEY=... AWS_REGION=...
modal deploy src/main.py
modal serve src/main.py   # dev

# Tests (venv python has runtime deps; pytest installed via uv)
./bin/python -m pytest test/ -q
```

`ffmpeg` must be on PATH (baked into the Modal image). Interactive docs: `/docs`.

## Video pipeline details

- Decode with `cv2.VideoCapture`; rejects unreadable files, unknown fps/dimensions, >4K frames, and videos longer than 1h.
- Write processed frames to a temp `.mp4` (`mp4v`), then one `ffmpeg` remux (see `src/lib/ffmpeg.py`): `-map 0:v:0 -map 1:a:0? -c:v libx264 -preset medium -crf 23 -c:a aac -shortest`. Silent inputs work; output is always H.264/AAC MP4.
- Filtered matching uses ArcFace normalized embeddings + cosine distance with the single shared `SIMILARITY_THRESHOLD = 0.3` (lower = same person; blur when `distance <= threshold`, keep the reference clear).
- `user_id` / `generation_id` isolate temp dirs, appear in logs, are echoed in the JSON body response and as `X-*` headers — but there is still no DB job table (no status polling yet).

## Limitations (as implemented)

- Filtered routes keep the matching face clear and blur the rest — no "blur only this person" mode.
- Endpoints are synchronous and block while the file processes (mitigated with a 30-min Modal timeout + per-request isolation, but no job queue / progress callbacks yet).
- Reference-face embeddings are cached in-process by content hash; no persistent vector DB.
- `test.py` is a manual webcam script, not part of the automated suite.

All items from `ai_suggestions.md` are implemented except the open product questions at its bottom (queue vs sync, blur-only-target mode, DB job tracking) — those need your call.
