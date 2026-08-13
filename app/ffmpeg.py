import subprocess
import json
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class FFmpegError(Exception):
    """Exception raised when FFmpeg operations fail"""
    pass


def check_ffmpeg_installed() -> bool:
    """Check if FFmpeg is installed and accessible"""
    try:
        subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            timeout=5,
            check=True
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return False


def check_ffprobe_installed() -> bool:
    """Check if ffprobe is installed and accessible"""
    try:
        subprocess.run(
            ["ffprobe", "-version"],
            capture_output=True,
            timeout=5,
            check=True
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return False


def get_audio_duration(audio_path: str) -> float:
    """
    Get duration of audio file in seconds using ffprobe
    
    Args:
        audio_path: Path to audio file (MP3)
        
    Returns:
        Duration in seconds as float
        
    Raises:
        FFmpegError: If ffprobe fails or file not found
    """
    audio_path_obj = Path(audio_path)
    
    if not audio_path_obj.exists():
        raise FFmpegError(f"Audio file not found: {audio_path}")
    
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1:noprint_wrappers=1",
                audio_path
            ],
            capture_output=True,
            text=True,
            timeout=10,
            check=True
        )
        
        duration = float(result.stdout.strip())
        logger.debug(f"Audio duration for {audio_path}: {duration}s")
        return duration
        
    except subprocess.CalledProcessError as e:
        logger.error(f"ffprobe error: {e.stderr}")
        raise FFmpegError(f"Failed to get duration of {audio_path}: {e.stderr}")
    except ValueError as e:
        logger.error(f"Failed to parse duration: {result.stdout}")
        raise FFmpegError(f"Failed to parse audio duration: {result.stdout}")
    except subprocess.TimeoutExpired:
        raise FFmpegError(f"ffprobe timeout for {audio_path}")


def get_image_dimensions(image_path: str) -> tuple:
    """
    Get image dimensions (width, height)
    
    Args:
        image_path: Path to image file
        
    Returns:
        Tuple of (width, height)
        
    Raises:
        FFmpegError: If ffprobe fails or file not found
    """
    image_path_obj = Path(image_path)
    
    if not image_path_obj.exists():
        raise FFmpegError(f"Image file not found: {image_path}")
    
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v", "error",
                "-select_streams", "v:0",
                "-show_entries", "stream=width,height",
                "-of", "csv=s=x:p=0",
                image_path
            ],
            capture_output=True,
            text=True,
            timeout=10,
            check=True
        )
        
        dimensions = result.stdout.strip().split("x")
        width, height = int(dimensions[0]), int(dimensions[1])
        logger.debug(f"Image dimensions for {image_path}: {width}x{height}")
        return (width, height)
        
    except subprocess.CalledProcessError as e:
        logger.error(f"ffprobe error: {e.stderr}")
        raise FFmpegError(f"Failed to get dimensions of {image_path}: {e.stderr}")
    except (ValueError, IndexError) as e:
        logger.error(f"Failed to parse dimensions: {result.stdout}")
        raise FFmpegError(f"Failed to parse image dimensions: {result.stdout}")
    except subprocess.TimeoutExpired:
        raise FFmpegError(f"ffprobe timeout for {image_path}")


def run_ffmpeg_command(command: list, timeout: int = 300) -> str:
    """
    Run FFmpeg command and return output
    
    Args:
        command: List of command arguments for FFmpeg
        timeout: Command timeout in seconds
        
    Returns:
        stdout from FFmpeg
        
    Raises:
        FFmpegError: If FFmpeg command fails
    """
    try:
        logger.debug(f"Running FFmpeg: {' '.join(command)}")
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=True
        )
        return result.stdout
        
    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg error: {e.stderr}")
        raise FFmpegError(f"FFmpeg command failed: {e.stderr}")
    except subprocess.TimeoutExpired:
        raise FFmpegError(f"FFmpeg command timeout after {timeout}s")
    except FileNotFoundError:
        raise FFmpegError("FFmpeg not found in system PATH")
