#!/usr/bin/env python3
"""
Test: Drawtext ONLY (tanpa zoompan) dengan subtitle test case dari user
Fokus pada masalah "No such filter:" yang user laporkan
"""

import logging
import tempfile
import subprocess
from pathlib import Path
from PIL import Image

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
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
    return "\n".join(lines)

def _escape_text_for_ffmpeg(text: str) -> str:
    text = text.replace("\\", "\\\\")
    text = text.replace('"', '\\"')
    text = text.replace(":", "\\:")
    text = text.replace("[", "\\[")
    text = text.replace("]", "\\]")
    text = text.replace("%", "\\%")
    return text

def test_drawtext_only():
    """Test drawtext filter ONLY (simple filter)"""
    
    logger.info(f"\n{'='*80}")
    logger.info("TEST: Drawtext ONLY (Simple Filter)")
    logger.info(f"{'='*80}")
    
    subtitle_text = "Hei, ingat waktu itu aku pinjemin uang untuk [tujuan]? Aku butuh untuk [kebutuhanmu sekarang]."
    duration = 2.0
    
    formatted_subtitle = _format_subtitle_text(subtitle_text)
    escaped_text = _escape_text_for_ffmpeg(formatted_subtitle)
    
    logger.info(f"Original: {repr(subtitle_text)}")
    logger.info(f"Formatted: {repr(formatted_subtitle)}")
    logger.info(f"Escaped: {repr(escaped_text)}")
    
    # Simple drawtext filter WITHOUT zoompan
    simple_filter = (
        f"scale={OUTPUT_WIDTH}:{OUTPUT_HEIGHT}:force_original_aspect_ratio=decrease,"
        f"pad={OUTPUT_WIDTH}:{OUTPUT_HEIGHT}:(ow-iw)/2:(oh-ih)/2:color=black,"
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
    
    logger.info(f"\nFilter (first 150 chars): {repr(simple_filter[:150])}...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        test_image = f"{temp_dir}/test_image.png"
        output_video = f"{temp_dir}/output.mp4"
        
        create_test_image(test_image)
        
        cmd = [
            "ffmpeg", "-y", "-loop", "1", "-i", test_image,
            "-vf", simple_filter, "-t", str(duration),
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-preset", "ultrafast", "-crf", "28",
            output_video
        ]
        
        logger.info(f"\nCommand list elements:")
        for i, arg in enumerate(cmd):
            if i == 6:  # -vf argument
                logger.info(f"  [{i}] '-vf'")
                logger.info(f"  [filter starts at index {i+1}]")
            elif i == 7:  # filter argument
                logger.info(f"  [{i}] (filter - length {len(arg)} chars)")
            elif len(repr(arg)) > 80:
                logger.info(f"  [{i}] {repr(arg[:60])}...")
            else:
                logger.info(f"  [{i}] {repr(arg)}")
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15, check=True)
            logger.info(f"\n✓ SUCCESS - Drawtext filter works!")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"\n✗ FAILED")
            if "No such filter:" in e.stderr:
                for line in e.stderr.split('\n'):
                    if "No such filter:" in line:
                        logger.error(f"Error: {line.strip()}")
            else:
                logger.error(f"Error: {e.stderr[:300]}")
            return False

if __name__ == "__main__":
    success = test_drawtext_only()
    logger.info(f"\n{'='*80}")
    logger.info(f"Result: {'PASS' if success else 'FAIL'}")
    logger.info(f"{'='*80}")
