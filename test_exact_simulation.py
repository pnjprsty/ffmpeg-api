#!/usr/bin/env python3
"""
Test: Simulasi EXACT alur dari app/renderer.py
Mensimulasikan _create_scene_video() method
"""

import logging
import tempfile
import subprocess
from pathlib import Path
from PIL import Image

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

OUTPUT_WIDTH = 1080
OUTPUT_HEIGHT = 1920
FPS = 30
SUBTITLE_FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

def create_test_image(output_path: str):
    img = Image.new('RGB', (OUTPUT_WIDTH, OUTPUT_HEIGHT), color=(73, 109, 137))
    img.save(output_path)

def _format_subtitle_text(text: str) -> str:
    """Exact copy dari app/renderer.py"""
    words = text.strip().split()
    lines = []
    current_line = []
    
    for word in words:
        test_line = " ".join(current_line + [word])
        if len(current_line) < 3 and len(test_line) <= 20:
            current_line.append(word)
        else:
            if current_line:
                lines.append(" ".join(current_line))
            current_line = [word]
    
    if current_line:
        lines.append(" ".join(current_line))
    
    formatted_text = "\n".join(lines)
    return formatted_text

def _escape_text_for_ffmpeg(text: str) -> str:
    """Exact copy dari app/renderer.py (ORIGINAL VERSION)"""
    text = text.replace("\\", "\\\\")
    text = text.replace('"', '\\"')
    text = text.replace(":", "\\:")
    text = text.replace("[", "\\[")
    text = text.replace("]", "\\]")
    text = text.replace("%", "\\%")
    return text

def run_ffmpeg_command(command: list, timeout: int = 300) -> str:
    """Exact copy dari app/ffmpeg.py"""
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
        raise Exception(f"FFmpeg command failed: {e.stderr}")
    except subprocess.TimeoutExpired:
        raise Exception(f"FFmpeg command timeout after {timeout}s")
    except FileNotFoundError:
        raise Exception("FFmpeg not found in system PATH")

def test_exact_simulation():
    """Test dengan EXACT simulasi dari app/renderer.py"""
    
    logger.info(f"\n{'='*80}")
    logger.info("EXACT SIMULATION OF app/renderer.py")
    logger.info(f"{'='*80}")
    
    subtitle_text = "Hei, ingat waktu itu aku pinjemin uang untuk [tujuan]? Aku butuh untuk [kebutuhanmu sekarang]."
    duration = 2.0
    scene_index = 0
    
    # Simulate exactly what _create_scene_video does
    logger.info(f"[Render] Creating scene video {scene_index+1}")
    
    with tempfile.TemporaryDirectory(prefix="video_render_") as temp_dir:
        scene_path = Path(temp_dir) / f"scene_{scene_index:03d}.mp4"
        
        # Step 1: Format subtitle
        formatted_subtitle = _format_subtitle_text(subtitle_text)
        escaped_text = _escape_text_for_ffmpeg(formatted_subtitle)
        
        # Log the subtitle transformation
        logger.info(f"[Render] Scene {scene_index+1} subtitle processing:")
        logger.info(f"[Render]   Original: {repr(subtitle_text)}")
        logger.info(f"[Render]   Formatted: {repr(formatted_subtitle)}")
        logger.info(f"[Render]   Escaped: {repr(escaped_text)}")
        
        # Step 2: Build ken burns parameters
        zoom_start = 1.0
        zoom_end = 1.05
        pan_x = 0.0
        pan_y = 0.02
        
        # Step 3: Build font_filter EXACTLY as in renderer.py
        font_filter = (
            f"scale={OUTPUT_WIDTH}:{OUTPUT_HEIGHT}:force_original_aspect_ratio=decrease,"
            f"pad={OUTPUT_WIDTH}:{OUTPUT_HEIGHT}:(ow-iw)/2:(oh-ih)/2:color=black,"
            f"zoompan=z='zoom+({zoom_end}-{zoom_start})/{duration}':"
            f"x='iw/2-(iw/zoom/2)+{pan_x}*t/{duration}':"
            f"y='ih/2-(ih/zoom/2)+{pan_y}*t/{duration}':"
            f"d={int(duration*FPS)}:s={OUTPUT_WIDTH}x{OUTPUT_HEIGHT},"
            f"fps={FPS},"
            f"drawtext=fontfile={SUBTITLE_FONT}:"
            f"text='{escaped_text}':"
            f"fontcolor=white:"
            f"fontsize=60:"
            f"borderw=3:"
            f"bordercolor=black:"
            f"shadowcolor=black:"
            f"shadowx=2:"
            f"shadowy=2:"
            f"box=1:"
            f"boxcolor=black@0.3:"
            f"boxborderw=10:"
            f"x=(w-text_w)/2:"
            f"y=h-text_h-100"
        )
        
        logger.info(f"[Render] Scene {scene_index+1} FFmpeg filter:")
        logger.info(f"[Render]   {repr(font_filter[:150])}...")
        
        # Create test image
        test_image = f"{temp_dir}/test_image.png"
        create_test_image(test_image)
        
        # Step 4: Build FFmpeg command EXACTLY as in renderer.py
        cmd = [
            "ffmpeg",
            "-y",
            "-loop", "1",
            "-i", test_image,
            "-vf", font_filter,
            "-t", str(duration),
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-preset", "medium",
            "-crf", "23",
            str(scene_path)
        ]
        
        logger.info(f"[Render] Full command:")
        for i, arg in enumerate(cmd):
            logger.info(f"  [{i}] {repr(arg[:80] if len(repr(arg)) > 80 else arg)}")
        
        # Step 5: Run FFmpeg command
        try:
            run_ffmpeg_command(cmd, timeout=60)
            logger.info(f"[Render] Scene {scene_index+1} video created: {scene_path}")
            logger.info(f"✓ SUCCESS")
            return True
        except Exception as e:
            logger.error(f"[Render] Failed to create scene video {scene_index+1}: {e}")
            logger.error(f"✗ FAILED")
            return False

if __name__ == "__main__":
    success = test_exact_simulation()
    logger.info(f"\n{'='*80}")
    logger.info(f"Result: {'PASS' if success else 'FAIL'}")
    logger.info(f"{'='*80}")
