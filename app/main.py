import logging
import os
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .models import RenderRequest, RenderResponse, ErrorResponse, Scene
from .ffmpeg import check_ffmpeg_installed, check_ffprobe_installed, FFmpegError
from .renderer import VideoRenderer
from .output_manager import setup_output_directory, OutputDirectoryError

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load configuration from .env file
from .config import settings

# Configuration from settings
OUTPUT_DIR = settings.get_output_dir()
RENDER_TIMEOUT = settings.get_render_timeout()

# Ensure output directory exists with proper permissions
try:
    setup_output_directory(OUTPUT_DIR)
    logger.info(f"Output directory ready: {OUTPUT_DIR}")
except OutputDirectoryError as e:
    logger.error(f"FATAL: Failed to setup output directory: {e}")
    
    # Provide helpful instructions for development/testing
    if OUTPUT_DIR == "/output":
        logger.info("\n" + "="*60)
        logger.info("DEVELOPMENT MODE: Using fallback directory /tmp/ffmpeg-output")
        logger.info("To use /output in production, edit .env file and set:")
        logger.info("  OUTPUT_DIR=/output")
        logger.info("Then setup /output with:")
        logger.info("  sudo mkdir -p /output")
        logger.info("  sudo chown $USER:$USER /output")
        logger.info("  sudo chmod 755 /output")
        logger.info("")
        logger.info("Current .env setting: OUTPUT_DIR=/output")
        logger.info("="*60 + "\n")
        
        # Fallback to writable directory for development
        OUTPUT_DIR = "/tmp/ffmpeg-output"
        try:
            setup_output_directory(OUTPUT_DIR)
            logger.info(f"Using development output directory: {OUTPUT_DIR}")
        except OutputDirectoryError as fallback_error:
            logger.error(f"Development fallback also failed: {fallback_error}")
            raise SystemExit(f"Cannot start service: {e}")
    else:
        raise SystemExit(f"Cannot start service: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown"""
    # Startup
    logger.info("Starting FFmpeg Video Renderer API")
    
    ffmpeg_ok = check_ffmpeg_installed()
    ffprobe_ok = check_ffprobe_installed()
    
    logger.info(f"FFmpeg available: {ffmpeg_ok}")
    logger.info(f"ffprobe available: {ffprobe_ok}")
    
    if not ffmpeg_ok or not ffprobe_ok:
        logger.error("FFmpeg or ffprobe not available!")
    
    yield
    
    # Shutdown
    logger.info("Shutting down FFmpeg Video Renderer API")


# Create FastAPI application
app = FastAPI(
    title="FFmpeg Video Renderer API",
    description="Convert scenes with images, audio, and subtitles into MP4 videos",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint
    Returns status of API and FFmpeg availability
    """
    ffmpeg_ok = check_ffmpeg_installed()
    ffprobe_ok = check_ffprobe_installed()
    
    if not ffmpeg_ok or not ffprobe_ok:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "unhealthy",
                "ffmpeg": ffmpeg_ok,
                "ffprobe": ffprobe_ok
            }
        )
    
    return {
        "status": "healthy",
        "ffmpeg": ffmpeg_ok,
        "ffprobe": ffprobe_ok,
        "output_dir": OUTPUT_DIR
    }


@app.post("/render", response_model=RenderResponse, tags=["Rendering"])
async def render_video(request: RenderRequest, background_tasks: BackgroundTasks):
    """
    Render video from scenes
    
    Request body contains:
    - ide: Unique identifier for the project
    - scenes: Array of scenes with image, voice, and subtitle
    
    Returns:
    - success: Whether rendering succeeded
    - ide: Project ID
    - filename: Output filename
    - output: Full path to output file
    - duration: Total video duration in seconds
    - scenes: Number of scenes processed
    """
    
    logger.info(f"[API] Render request received: ide={request.ide}, scenes={len(request.scenes)}")
    
    # Validate request
    if not request.ide or len(request.ide.strip()) == 0:
        logger.error("[API] Invalid ide: empty")
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error": "ide cannot be empty"
            }
        )
    
    if not request.scenes or len(request.scenes) == 0:
        logger.error("[API] Invalid scenes: empty array")
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error": "scenes array cannot be empty"
            }
        )
    
    # Validate each scene
    for i, scene in enumerate(request.scenes):
        if not scene.image or len(scene.image.strip()) == 0:
            logger.error(f"[API] Scene {i+1} has empty image path")
            raise HTTPException(
                status_code=400,
                detail={
                    "success": False,
                    "error": f"Scene {i+1}: image path cannot be empty"
                }
            )
        
        if not scene.voice or len(scene.voice.strip()) == 0:
            logger.error(f"[API] Scene {i+1} has empty voice path")
            raise HTTPException(
                status_code=400,
                detail={
                    "success": False,
                    "error": f"Scene {i+1}: voice path cannot be empty"
                }
            )
        
        if not scene.subtitleText or len(scene.subtitleText.strip()) == 0:
            logger.error(f"[API] Scene {i+1} has empty subtitle")
            raise HTTPException(
                status_code=400,
                detail={
                    "success": False,
                    "error": f"Scene {i+1}: subtitleText cannot be empty"
                }
            )
        
        # Check if image exists
        image_path = Path(scene.image)
        if not image_path.exists():
            logger.error(f"[API] Scene {i+1} image not found: {scene.image}")
            raise HTTPException(
                status_code=400,
                detail={
                    "success": False,
                    "error": f"Scene {i+1} image file not found",
                    "path": scene.image
                }
            )
        
        # Check if voice exists
        voice_path = Path(scene.voice)
        if not voice_path.exists():
            logger.error(f"[API] Scene {i+1} voice not found: {scene.voice}")
            raise HTTPException(
                status_code=400,
                detail={
                    "success": False,
                    "error": f"Scene {i+1} voice file not found",
                    "path": scene.voice
                }
            )
    
    # Check output file doesn't already exist or handle it
    output_filename = f"{request.ide}.mp4"
    output_path = Path(OUTPUT_DIR) / output_filename
    
    logger.info(f"[API] Starting rendering process")
    
    try:
        # Perform rendering in thread pool
        with VideoRenderer(output_dir=OUTPUT_DIR) as renderer:
            output_file, total_duration = await renderer.render(
                request.ide,
                request.scenes
            )
        
        logger.info(f"[API] Rendering completed successfully: {output_file}")
        
        return RenderResponse(
            success=True,
            ide=request.ide,
            filename=output_filename,
            output=output_file,
            duration=total_duration,
            scenes=len(request.scenes)
        )
        
    except FFmpegError as e:
        logger.error(f"[API] FFmpeg error: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": f"Rendering failed: {str(e)}"
            }
        )
    except Exception as e:
        logger.error(f"[API] Unexpected error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": f"Unexpected error: {str(e)}"
            }
        )


@app.get("/video/{filename}", tags=["Output"])
async def get_video(filename: str):
    """
    Download rendered video file
    
    Args:
        filename: Name of the video file (e.g., "6a7bf3535d2ed1a7a4c5e23e.mp4")
    
    Returns:
        Video file as MP4
    """
    
    # Validate filename - only allow alphanumeric, dash, underscore
    import re
    if not re.match(r"^[a-zA-Z0-9_\-]+\.mp4$", filename):
        logger.warning(f"[API] Invalid filename requested: {filename}")
        raise HTTPException(status_code=400, detail="Invalid filename format")
    
    file_path = Path(OUTPUT_DIR) / filename
    
    # Check if file exists
    if not file_path.exists():
        logger.warning(f"[API] Video file not found: {filename}")
        raise HTTPException(status_code=404, detail="Video file not found")
    
    logger.info(f"[API] Serving video file: {filename}")
    
    return FileResponse(
        path=file_path,
        media_type="video/mp4",
        filename=filename
    )


@app.get("/", tags=["Info"])
async def root():
    """
    API information and usage
    """
    return {
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )
