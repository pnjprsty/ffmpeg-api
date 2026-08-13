# FFmpeg Video Renderer API - Quick Start Guide

## Installation & Setup (5 minutes)

### Prerequisites

- Python 3.12+ (or 3.10+)
- FFmpeg 4.2+
- DejaVu fonts (for subtitles)

### Step 1: Install System Dependencies (Ubuntu/Debian)

```bash
sudo apt-get update
sudo apt-get install -y ffmpeg fonts-dejavu python3-pip
```

### Step 2: Install Python Dependencies

```bash
cd /home/gli-panji/tools/ffmpeg-api
pip install -r requirements.txt
```

### Step 3: Verify Installation

```bash
python3 test_api.py
```

You should see:
```
✓ PASS - FFmpeg Check
✓ PASS - Python Imports
✓ PASS - Directory Structure
✓ PASS - Docker Configuration
```

## Running the API

### Option A: Local Development

```bash
cd /home/gli-panji/tools/ffmpeg-api
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

API will be available at: **http://localhost:8000**

Interactive docs: **http://localhost:8000/docs**

### Option B: Docker (Recommended for Production)

```bash
cd /home/gli-panji/tools/ffmpeg-api
docker-compose up -d
```

View logs:
```bash
docker-compose logs -f ffmpeg-api
```

Stop:
```bash
docker-compose down
```

## Testing the API

### 1. Health Check

```bash
curl -X GET http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "ffmpeg": true,
  "ffprobe": true,
  "output_dir": "/output"
}
```

### 2. Render a Video

Using the provided example request:

```bash
curl -X POST http://localhost:8000/render \
  -H "Content-Type: application/json" \
  -d @request.json
```

Or with a custom request:

```bash
curl -X POST http://localhost:8000/render \
  -H "Content-Type: application/json" \
  -d '{
    "ide": "my-video-001",
    "scenes": [
      {
        "type": "hook",
        "image": "/home/gli-panji/generated-images/image1.jpg",
        "voice": "/home/gli-panji/generated-images/audio1.mp3",
        "subtitleText": "First scene subtitle"
      }
    ]
  }'
```

Expected response:
```json
{
  "success": true,
  "ide": "my-video-001",
  "filename": "my-video-001.mp4",
  "output": "/output/my-video-001.mp4",
  "duration": 5.42,
  "scenes": 1
}
```

### 3. Download the Video

```bash
curl -O http://localhost:8000/video/my-video-001.mp4
```

## Project Structure

```
/home/gli-panji/tools/ffmpeg-api/
├── app/
│   ├── __init__.py              # Package init
│   ├── main.py                  # FastAPI app & endpoints
│   ├── models.py                # Pydantic models
│   ├── ffmpeg.py                # FFmpeg utilities
│   └── renderer.py              # Video rendering engine
├── output/                      # Rendered videos (shared with Docker)
├── requirements.txt             # Python dependencies
├── Dockerfile                   # Docker image
├── docker-compose.yml           # Docker Compose config
├── .dockerignore               # Docker build exclusions
├── test_api.py                 # System test script
├── request.json                # Example API request
├── README.md                   # Full documentation
└── QUICKSTART.md              # This file
```

## API Endpoints Summary

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | GET | API info & endpoints |
| `/health` | GET | Health check |
| `/render` | POST | Render video from scenes |
| `/video/{filename}` | GET | Download rendered video |
| `/docs` | GET | Swagger UI docs |
| `/openapi.json` | GET | OpenAPI schema |

## Key Features

✅ **Scene Duration**: Automatically matches audio duration (no fixed 5-10 sec)
✅ **Subtitles**: Rendered with white bold text, black outline, positioned at bottom
✅ **Ken Burns Effect**: Subtle zoom + pan on images for visual interest
✅ **Transitions**: xfade transitions between scenes (fade, smoothleft, etc.)
✅ **Audio Sync**: Audio tracks concatenated without gaps
✅ **Portrait Format**: 1080x1920 resolution, 30 FPS
✅ **Error Validation**: Comprehensive file and parameter validation
✅ **Async Processing**: Non-blocking rendering
✅ **Docker Ready**: Complete containerization with all dependencies

## Configuration

### Environment Variables

```bash
export OUTPUT_DIR=/output              # Output directory for videos
export RENDER_TIMEOUT=300              # Render timeout in seconds
```

### Docker Environment

Edit `docker-compose.yml`:
```yaml
environment:
  OUTPUT_DIR: /output
  RENDER_TIMEOUT: 300
```

## Troubleshooting

### "FFmpeg not found"
```bash
ffmpeg -version  # Check if installed
sudo apt-get install ffmpeg  # Install if missing
```

### "Font file not found"
```bash
sudo apt-get install fonts-dejavu
```

### Permission denied on output directory
```bash
chmod 777 ./output
```

### Port 8000 already in use
```bash
# Use different port
uvicorn app.main:app --host 0.0.0.0 --port 8001
```

### Video rendering fails
1. Verify image file exists and is readable
2. Verify MP3 file exists and is valid: `ffprobe /path/to/audio.mp3`
3. Check disk space: `df -h`
4. Review API logs for FFmpeg error messages

## Common Use Cases

### Basic Single Scene

```json
{
  "ide": "scene-001",
  "scenes": [
    {
      "type": "hook",
      "image": "/path/to/image.jpg",
      "voice": "/path/to/audio.mp3",
      "subtitleText": "Your subtitle here"
    }
  ]
}
```

### Multiple Scenes with Different Types

```json
{
  "ide": "complete-story",
  "scenes": [
    {
      "type": "hook",
      "image": "/path/to/intro.jpg",
      "voice": "/path/to/intro.mp3",
      "subtitleText": "Introduction"
    },
    {
      "type": "context",
      "image": "/path/to/context.jpg",
      "voice": "/path/to/context.mp3",
      "subtitleText": "What's happening"
    },
    {
      "type": "problem",
      "image": "/path/to/problem.jpg",
      "voice": "/path/to/problem.mp3",
      "subtitleText": "The issue"
    },
    {
      "type": "advice",
      "image": "/path/to/solution.jpg",
      "voice": "/path/to/solution.mp3",
      "subtitleText": "How to solve it"
    }
  ]
}
```

### With n8n Integration

In n8n HTTP Request node:

**Method**: POST
**URL**: `http://ffmpeg-api:8000/render`
**Headers**: `Content-Type: application/json`
**Body**:
```json
{
  "ide": "{{ $node['previous_node'].json.project_id }}",
  "scenes": "{{ $node['previous_node'].json.scenes }}"
}
```

## Next Steps

1. Read [`README.md`](README.md) for comprehensive documentation
2. Check [`app/models.py`](app/models.py:1) for data schema
3. Explore [`app/main.py`](app/main.py:1) for endpoint implementation
4. Review [`app/renderer.py`](app/renderer.py:18) for rendering logic
5. Test with your own images and audio files

## Performance Notes

- First render takes longer (font loading, cache warming)
- Subsequent renders are faster
- Each scene is processed sequentially
- Total time = (sum of all scene audio durations) + processing overhead
- Adjust CRF in [`app/renderer.py`](app/renderer.py:169) for quality/speed tradeoff

## Support Resources

- **Full Docs**: See [`README.md`](README.md)
- **API Docs**: Visit `http://localhost:8000/docs`
- **Troubleshooting**: See README.md "Troubleshooting" section
- **Examples**: See `request.json` for example payload

---

**Ready?** Start with:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Then visit: **http://localhost:8000/docs**

Enjoy rendering! 🎬✨
