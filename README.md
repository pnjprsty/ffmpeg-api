# FFmpeg Video Renderer API

A Python FastAPI service that renders video compositions from scenes containing images, audio, and subtitle text. Designed for automated video production workflows with support for n8n integration.

## Features

- **Automated Video Rendering**: Convert multiple scenes (images + audio) into a single MP4 video
- **Dynamic Subtitle Support**: Automatic subtitle rendering with customizable styling
- **Ken Burns Effect**: Subtle zoom and pan effects on images for visual interest
- **Smooth Transitions**: xfade transitions between scenes with configurable duration
- **Adaptive Scene Duration**: Each scene duration matches its audio file exactly
- **Portrait Format**: Output videos in 1080x1920 resolution (ideal for mobile/vertical content)
- **Error Validation**: Comprehensive validation of input files and parameters
- **Async Processing**: Non-blocking rendering using async/thread pool
- **Docker Support**: Complete containerization with FFmpeg and dependencies included

## Project Structure

```
ffmpeg-api/
├── app/
│   ├── __init__.py          # Package initialization
│   ├── main.py              # FastAPI application and endpoints
│   ├── models.py            # Pydantic data models
│   ├── ffmpeg.py            # FFmpeg utilities (ffprobe, version checks)
│   └── renderer.py          # Video rendering engine
├── output/                  # Directory for rendered MP4 files
├── requirements.txt         # Python dependencies
├── Dockerfile              # Docker image definition
├── docker-compose.yml      # Docker Compose configuration
├── .dockerignore           # Files to exclude from Docker build
└── README.md               # This file
```

## Requirements

### Local Installation

- **Python**: 3.12+
- **FFmpeg**: 4.2+
- **ffprobe**: (included with FFmpeg)
- **System fonts**: DejaVu Sans Bold (for subtitles)

### Docker Installation

- **Docker**: 20.10+
- **Docker Compose**: 2.0+

## Installation

### Option 1: Local Installation

#### 1. Install System Dependencies (Ubuntu/Debian)

```bash
sudo apt-get update
sudo apt-get install -y ffmpeg fonts-dejavu
```

#### 2. Install Python Dependencies

```bash
cd /path/to/ffmpeg-api
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

#### 3. Verify Installation

```bash
ffmpeg -version
ffprobe -version
python -m compileall app
```

### Option 2: Docker Installation

```bash
cd /path/to/ffmpeg-api
docker-compose build
```

## Running the API

### Local Development

```bash
cd /path/to/ffmpeg-api
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

API will be available at: `http://localhost:8000`

### Docker

```bash
docker-compose up -d
```

View logs:
```bash
docker-compose logs -f ffmpeg-api
```

## API Endpoints

### 1. Health Check

```http
GET /health
```

**Response (200 OK)**:
```json
{
  "status": "healthy",
  "ffmpeg": true,
  "ffprobe": true,
  "output_dir": "/output"
}
```

**Response (503 Service Unavailable)**:
```json
{
  "status": "unhealthy",
  "ffmpeg": false,
  "ffprobe": true
}
```

### 2. Render Video

```http
POST /render
Content-Type: application/json
```

**Request Body**:
```json
{
  "ide": "6a7bf3535d2ed1a7a4c5e23e",
  "scenes": [
    {
      "type": "hook",
      "image": "/home/gli-panji/generated-images/tipsbijak/tipsbijak-2026-08-12_223143.jpg",
      "voice": "/home/gli-panji/generated-images/tipsbijak/tipsbijak-voice-2026-08-12_223145.mp3",
      "subtitleText": "Teman sering minta pinjam uang, tapi lupa bayar?"
    },
    {
      "type": "context",
      "image": "/home/gli-panji/generated-images/tipsbijak/tipsbijak-2026-08-12_223150.jpg",
      "voice": "/home/gli-panji/generated-images/tipsbijak/tipsbijak-voice-2026-08-12_223151.mp3",
      "subtitleText": "Mengingatkan tentang utang bisa terasa canggung"
    }
  ]
}
```

**Response (200 OK)**:
```json
{
  "success": true,
  "ide": "6a7bf3535d2ed1a7a4c5e23e",
  "filename": "6a7bf3535d2ed1a7a4c5e23e.mp4",
  "output": "/output/6a7bf3535d2ed1a7a4c5e23e.mp4",
  "duration": 28.45,
  "scenes": 2
}
```

**Response (400 Bad Request)**:
```json
{
  "success": false,
  "error": "Scene 1 image file not found",
  "path": "/path/to/missing/image.jpg"
}
```

**Response (500 Internal Server Error)**:
```json
{
  "success": false,
  "error": "Rendering failed: FFmpeg error message"
}
```

### 3. Download Video

```http
GET /video/{filename}
```

**Example**:
```http
GET /video/6a7bf3535d2ed1a7a4c5e23e.mp4
```

**Response**: MP4 video file with `Content-Type: video/mp4`

**Response (404 Not Found)**:
```json
{"detail": "Video file not found"}
```

### 4. API Information

```http
GET /
```

**Response**:
```json
{
  "name": "FFmpeg Video Renderer API",
  "version": "1.0.0",
  "description": "Convert scenes with images, audio, and subtitles into MP4 videos",
  "endpoints": {
    "health": "GET /health",
    "render": "POST /render",
    "download": "GET /video/{filename}",
    "docs": "/docs",
    "openapi": "/openapi.json"
  }
}
```

## Usage Examples

### cURL

#### Health Check

```bash
curl -X GET http://localhost:8000/health
```

#### Render Video

```bash
curl -X POST http://localhost:8000/render \
  -H "Content-Type: application/json" \
  -d '{
    "ide": "test-video-001",
    "scenes": [
      {
        "type": "hook",
        "image": "/home/gli-panji/generated-images/test/image1.jpg",
        "voice": "/home/gli-panji/generated-images/test/audio1.mp3",
        "subtitleText": "This is the first scene"
      }
    ]
  }'
```

#### Download Video

```bash
curl -O http://localhost:8000/video/test-video-001.mp4
```

### Python Requests

```python
import requests
import json

# Render video
url = "http://localhost:8000/render"
payload = {
    "ide": "python-test-001",
    "scenes": [
        {
            "type": "hook",
            "image": "/path/to/image.jpg",
            "voice": "/path/to/audio.mp3",
            "subtitleText": "Test subtitle"
        }
    ]
}

response = requests.post(url, json=payload)
result = response.json()

if result["success"]:
    print(f"Video created: {result['output']}")
    print(f"Duration: {result['duration']}s")
else:
    print(f"Error: {result['error']}")

# Download video
video_url = f"http://localhost:8000/video/{result['filename']}"
video_response = requests.get(video_url)
with open("output.mp4", "wb") as f:
    f.write(video_response.content)
```

### n8n Integration

#### 1. HTTP Request Node (GET Health)

- **Method**: GET
- **URL**: `http://ffmpeg-api:8000/health`

#### 2. HTTP Request Node (POST Render)

- **Method**: POST
- **URL**: `http://ffmpeg-api:8000/render`
- **Headers**: `Content-Type: application/json`
- **Body** (JSON):
```json
{
  "ide": "{{ $node['previous_node'].json.project_id }}",
  "scenes": "{{ $node['previous_node'].json.scenes }}"
}
```

#### 3. HTTP Request Node (GET Video)

- **Method**: GET
- **URL**: `http://ffmpeg-api:8000/video/{{ $node['Render'].json.filename }}`
- **Response type**: Binary data

## Configuration

### Environment Variables

- **OUTPUT_DIR**: Directory for rendered videos (default: `/output`)
- **RENDER_TIMEOUT**: Rendering timeout in seconds (default: `300`)

**Example**:
```bash
export OUTPUT_DIR=/mnt/videos
export RENDER_TIMEOUT=600
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Docker Environment

Edit `docker-compose.yml`:

```yaml
environment:
  OUTPUT_DIR: /output
  RENDER_TIMEOUT: 300
```

## Video Output Specifications

- **Resolution**: 1080x1920 (portrait, vertical)
- **FPS**: 30 frames per second
- **Codec**: H.264 (libx264)
- **Audio Codec**: AAC
- **Audio Bitrate**: 192 kbps
- **Color Space**: YUV 4:2:0
- **Container**: MP4
- **Output Quality**: CRF 23 (good balance between quality and file size)

## Subtitle Styling

Subtitles are rendered with:
- **Font**: DejaVu Sans Bold
- **Color**: White (#FFFFFF)
- **Font Size**: 60px (automatically scaled for 1080x1920)
- **Border Width**: 3px
- **Border Color**: Black (#000000)
- **Shadow**: Yes (2px offset)
- **Background**: Semi-transparent black box
- **Position**: Bottom of screen with 100px margin
- **Alignment**: Centered horizontally

## Image Processing

- **Scale Method**: `force_original_aspect_ratio=cover` (no distortion)
- **Effect**: Ken Burns (subtle zoom + pan)
  - Zoom: +5% over scene duration
  - Pan: Slight vertical movement for depth
  - Fallback to static image if effect fails
- **Transition**: xfade with 0.4 second duration between scenes

## Scene Duration Handling

- Each scene duration is determined by its audio file duration (via ffprobe)
- Image is displayed for the exact duration of its audio
- Transitions overlap by 0.4 seconds (audio continues through transition)
- Total video duration = sum of all audio durations - (number_of_scenes - 1) × 0.4

**Example**:
```
Scene 1 audio: 3.42s
Scene 2 audio: 4.87s
Scene 3 audio: 5.21s

Total scenes: 3
Transitions: 2 (between scenes)
Total duration: (3.42 + 4.87 + 5.21) - (2 × 0.4) = 12.7s
```

## Error Handling

### Validation Errors

The API validates all input before processing:

1. **Empty `ide`**: HTTP 400 - "ide cannot be empty"
2. **Empty `scenes` array**: HTTP 400 - "scenes array cannot be empty"
3. **Missing image path**: HTTP 400 - "Scene X: image path cannot be empty"
4. **Missing voice path**: HTTP 400 - "Scene X: voice path cannot be empty"
5. **Missing subtitle**: HTTP 400 - "Scene X: subtitleText cannot be empty"
6. **Image file not found**: HTTP 400 - Error with path information
7. **Audio file not found**: HTTP 400 - Error with path information

### Processing Errors

If FFmpeg fails during rendering:

```json
{
  "success": false,
  "error": "Rendering failed: [FFmpeg error message]"
}
```

Common causes:
- Corrupted image or audio file
- Unsupported image format
- Unsupported audio codec
- Insufficient disk space
- Missing fonts or system libraries

## Docker Usage

### Building the Image

```bash
docker-compose build
```

### Running the Container

```bash
docker-compose up -d
```

### Stopping the Container

```bash
docker-compose down
```

### Viewing Logs

```bash
docker-compose logs -f ffmpeg-api
```

### Rebuilding After Code Changes

```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Accessing Container Shell

```bash
docker exec -it ffmpeg-video-renderer /bin/bash
```

### Volume Mounts

The `docker-compose.yml` mounts:

- **`/home/gli-panji/generated-images`** (read-only): Input directory for images and audio
- **`./output:/output`** (read-write): Output directory for rendered videos

Ensure paths in your JSON payloads use the absolute paths inside the container.

## Troubleshooting

### "FFmpeg not found"

**Local**: Install FFmpeg
```bash
sudo apt-get install ffmpeg  # Ubuntu/Debian
brew install ffmpeg          # macOS
```

**Docker**: Rebuild image
```bash
docker-compose build --no-cache
```

### "Image file not found"

- Verify the absolute path is correct
- Check file permissions (API needs read access)
- In Docker, ensure the path exists in the mounted volume

### "Failed to get duration of audio"

- Audio file may be corrupted
- Verify MP3 file with: `ffprobe /path/to/audio.mp3`
- Try re-encoding the audio file

### "Font file not found"

**Local**:
```bash
sudo apt-get install fonts-dejavu
```

**Docker**: Fonts are installed during build; rebuild image

### "Rendering timeout"

- Increase `RENDER_TIMEOUT` environment variable
- Check if system has sufficient resources (CPU, disk space, RAM)
- Verify FFmpeg process isn't hung: `ps aux | grep ffmpeg`

### Permission Denied

**Local**:
- Ensure output directory is writable: `chmod 755 ./output`

**Docker**:
- Check volume mount permissions
- Try running with elevated privileges (not recommended for production)

### Out of Disk Space

- Check available space: `df -h`
- Clean old video files: `rm ./output/*.mp4`
- Increase disk capacity

## Performance Considerations

- **CPU-intensive**: Video rendering uses significant CPU
- **Non-blocking**: API uses async/thread pool to avoid blocking
- **Single render**: Current implementation processes one render at a time
- **Temporary files**: Intermediate files are cleaned up automatically
- **Resolution impact**: 1080x1920 at 30 FPS is demanding; adjust CRF if needed

For high-volume rendering, consider:
- Running multiple API instances with load balancing
- Implementing a job queue system
- Using GPU-accelerated encoding (requires NVIDIA)

## API Documentation

Interactive API documentation available at:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI JSON**: `http://localhost:8000/openapi.json`

## Logging

API logs are output to stdout:

```
2026-08-13 12:34:56,789 - app.main - INFO - Starting FFmpeg Video Renderer API
2026-08-13 12:34:57,012 - app.ffmpeg - INFO - FFmpeg available: True
2026-08-13 12:35:01,234 - app.renderer - INFO - [Render] Starting render: 6a7bf3535d2ed1a7a4c5e23e
2026-08-13 12:35:02,456 - app.renderer - INFO - [Render] Scene 1/2 - Duration: 3.42s
```

**Docker logging**:
```bash
docker-compose logs ffmpeg-api
```

## Development

### Code Quality

```bash
# Compile check
python -m compileall app

# Run on file change
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Adding Features

Existing structure supports:
- Additional scene types: Add to [`SceneType`](app/models.py:10) enum
- New transitions: Update transition list in [`_concatenate_with_transitions`](app/renderer.py:200)
- Custom subtitle styling: Modify filter string in [`_create_scene_video`](app/renderer.py:99)
- New output formats: Extend [`VideoRenderer`](app/renderer.py:18) class

## License

This project is provided as-is for integration with n8n workflows.

## Support

For issues or questions:
1. Check the Troubleshooting section above
2. Review API logs: `docker-compose logs ffmpeg-api`
3. Test with simple single-scene videos first
4. Verify FFmpeg works locally: `ffmpeg -f lavfi -i testsrc=s=1080x1920:d=1 test.mp4`
