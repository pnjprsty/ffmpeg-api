#!/usr/bin/env python3
"""
Deep dive debugging subtitle rendering FFmpeg
Mensimulasikan alur lengkap dari subtitle text -> escaped -> filter -> command -> subprocess
"""

import logging
import tempfile
import subprocess
from pathlib import Path
from PIL import Image
import shlex

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

OUTPUT_WIDTH = 1080
OUTPUT_HEIGHT = 1920
FPS = 30
SUBTITLE_FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

def create_test_image(output_path: str):
    """Create a simple test image"""
    img = Image.new('RGB', (OUTPUT_WIDTH, OUTPUT_HEIGHT), color=(73, 109, 137))
    img.save(output_path)

def escape_text_for_ffmpeg(text: str) -> str:
    """Escape text for FFmpeg drawtext filter (current version)"""
    text = text.replace("\\", "\\\\")
    text = text.replace('"', '\\"')
    text = text.replace(":", "\\:")
    text = text.replace("[", "\\[")
    text = text.replace("]", "\\]")
    text = text.replace("%", "\\%")
    return text

def format_subtitle_text(text: str) -> str:
    """Format subtitle text"""
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

def test_filter_construction_issue():
    """Test how filter construction might be causing issue"""
    
    subtitle_text = "Hei, ingat waktu itu aku pinjemin uang untuk [tujuan]? Aku butuh untuk [kebutuhanmu sekarang]."
    
    logger.info(f"\n{'='*80}")
    logger.info(f"TEST: Filter Construction Issue Analysis")
    logger.info(f"{'='*80}")
    
    # Step 1: Format
    formatted = format_subtitle_text(subtitle_text)
    logger.info(f"\nStep 1 - Formatted text:")
    logger.info(repr(formatted))
    
    # Step 2: Escape
    escaped = escape_text_for_ffmpeg(formatted)
    logger.info(f"\nStep 2 - Escaped text:")
    logger.info(repr(escaped))
    
    # Step 3: Build filter - Approach A (current)
    filter_approach_a = (
        f"scale={OUTPUT_WIDTH}:{OUTPUT_HEIGHT}:force_original_aspect_ratio=decrease,"
        f"pad={OUTPUT_WIDTH}:{OUTPUT_HEIGHT}:(ow-iw)/2:(oh-ih)/2:color=black,"
        f"fps={FPS},"
        f"drawtext=fontfile={SUBTITLE_FONT}:"
        f"text='{escaped}':"
        f"fontcolor=white:"
        f"fontsize=60:"
        f"x=(w-text_w)/2:"
        f"y=h-text_h-100"
    )
    
    # Step 3: Build filter - Approach B (proposed fix: use double quotes but escape differently)
    # When using double quotes, newlines need special handling
    # Option 1: Replace newlines with escaped newlines for double-quoted strings
    escaped_for_double_quotes = escaped.replace("\n", "\\n")
    filter_approach_b = (
        f"scale={OUTPUT_WIDTH}:{OUTPUT_HEIGHT}:force_original_aspect_ratio=decrease,"
        f"pad={OUTPUT_WIDTH}:{OUTPUT_HEIGHT}:(ow-iw)/2:(oh-ih)/2:color=black,"
        f"fps={FPS},"
        f"drawtext=fontfile={SUBTITLE_FONT}:"
        f"text=\"{escaped_for_double_quotes}\":"
        f"fontcolor=white:"
        f"fontsize=60:"
        f"x=(w-text_w)/2:"
        f"y=h-text_h-100"
    )
    
    logger.info(f"\nStep 3 - Filter Approach A (single quotes, actual newlines):")
    logger.info(repr(filter_approach_a))
    
    logger.info(f"\nStep 3 - Filter Approach B (double quotes, escaped newlines):")
    logger.info(repr(filter_approach_b))
    
    # Step 4: Test both approaches
    output_dir = "/tmp/ffmpeg_deep_debug"
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    test_image = f"{output_dir}/test_image.png"
    create_test_image(test_image)
    
    approaches = [
        ("A: Single quotes with actual newlines", filter_approach_a),
        ("B: Double quotes with escaped newlines", filter_approach_b),
    ]
    
    for approach_name, filter_expr in approaches:
        logger.info(f"\n{'='*80}")
        logger.info(f"Testing {approach_name}")
        logger.info(f"{'='*80}")
        
        output_video = f"{output_dir}/output_{approach_name.replace(': ', '_').replace(' ', '_')}.mp4"
        
        # Build command as list (like subprocess will use)
        cmd = [
            "ffmpeg",
            "-y",
            "-loop", "1",
            "-i", test_image,
            "-vf", filter_expr,
            "-t", "2",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-preset", "ultrafast",
            "-crf", "28",
            output_video
        ]
        
        logger.info(f"\nCommand as list (for subprocess):")
        for i, arg in enumerate(cmd):
            logger.info(f"  [{i}] {repr(arg)}")
        
        logger.info(f"\nCommand as shell string:")
        logger.info(f"  {' '.join(shlex.quote(arg) for arg in cmd)}")
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            
            if result.returncode == 0:
                logger.info(f"✓ SUCCESS")
            else:
                logger.error(f"✗ FAILED")
                # Extract the key error
                if "No such filter:" in result.stderr:
                    lines = result.stderr.split('\n')
                    for line in lines:
                        if "No such filter:" in line:
                            logger.error(f"  Error: {line.strip()}")
                else:
                    logger.error(f"  stderr: {result.stderr[:500]}")
        except Exception as e:
            logger.error(f"✗ EXCEPTION: {e}")

if __name__ == "__main__":
    test_filter_construction_issue()
