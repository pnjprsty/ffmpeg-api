#!/usr/bin/env python3
"""
Test subtitle rendering dengan berbagai karakter khusus
untuk debug filter drawtext FFmpeg
"""

import logging
import tempfile
from pathlib import Path
from PIL import Image
import subprocess
import sys

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Video configuration constants
OUTPUT_WIDTH = 1080
OUTPUT_HEIGHT = 1920
FPS = 30
SUBTITLE_FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

def create_test_image(output_path: str, width: int = 1080, height: int = 1920):
    """Create a simple test image"""
    img = Image.new('RGB', (width, height), color=(73, 109, 137))
    img.save(output_path)
    logger.info(f"Created test image: {output_path}")

def escape_text_for_ffmpeg(text: str) -> str:
    """
    Escape text for FFmpeg drawtext filter.
    """
    # Backslash must be escaped first
    text = text.replace("\\", "\\\\")
    
    # Escape double quotes because drawtext text= uses double quotes
    text = text.replace('"', '\\"')
    
    # Escape FFmpeg filter separator
    text = text.replace(":", "\\:")
    
    # Escape filtergraph special characters
    text = text.replace("[", "\\[")
    text = text.replace("]", "\\]")
    
    # Escape percent
    text = text.replace("%", "\\%")
    
    return text

def format_subtitle_text(text: str) -> str:
    """Format subtitle text with line breaks"""
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

def test_drawtext_filter(subtitle_text: str, test_name: str, output_dir: str = "/tmp"):
    """Test drawtext filter dengan berbagai approaches"""
    
    logger.info(f"\n{'='*80}")
    logger.info(f"TEST: {test_name}")
    logger.info(f"{'='*80}")
    
    # Step 1: Format subtitle
    formatted_subtitle = format_subtitle_text(subtitle_text)
    logger.info(f"Step 1 - Formatted subtitle:\n{repr(formatted_subtitle)}")
    
    # Step 2: Escape for FFmpeg
    escaped_text = escape_text_for_ffmpeg(formatted_subtitle)
    logger.info(f"Step 2 - Escaped text:\n{repr(escaped_text)}")
    
    # Create test image
    test_image = f"{output_dir}/test_image_{test_name}.png"
    test_output = f"{output_dir}/test_output_{test_name}.mp4"
    
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    create_test_image(test_image)
    
    # Step 3: Build drawtext filter dengan different quoting approaches
    
    # Approach 1: Single quotes (current)
    filter_v1 = (
        f"scale={OUTPUT_WIDTH}:{OUTPUT_HEIGHT}:force_original_aspect_ratio=decrease,"
        f"pad={OUTPUT_WIDTH}:{OUTPUT_HEIGHT}:(ow-iw)/2:(oh-ih)/2:color=black,"
        f"fps={FPS},"
        f"drawtext=fontfile={SUBTITLE_FONT}:"
        f"text='{escaped_text}':"
        f"fontcolor=white:"
        f"fontsize=60:"
        f"x=(w-text_w)/2:"
        f"y=h-text_h-100"
    )
    
    # Approach 2: Double quotes
    filter_v2 = (
        f"scale={OUTPUT_WIDTH}:{OUTPUT_HEIGHT}:force_original_aspect_ratio=decrease,"
        f"pad={OUTPUT_WIDTH}:{OUTPUT_HEIGHT}:(ow-iw)/2:(oh-ih)/2:color=black,"
        f"fps={FPS},"
        f"drawtext=fontfile={SUBTITLE_FONT}:"
        f"text=\"{escaped_text}\":"
        f"fontcolor=white:"
        f"fontsize=60:"
        f"x=(w-text_w)/2:"
        f"y=h-text_h-100"
    )
    
    # Approach 3: Escape single quote in drawtext value
    filter_v3 = (
        f"scale={OUTPUT_WIDTH}:{OUTPUT_HEIGHT}:force_original_aspect_ratio=decrease,"
        f"pad={OUTPUT_WIDTH}:{OUTPUT_HEIGHT}:(ow-iw)/2:(oh-ih)/2:color=black,"
        f"fps={FPS},"
        f"drawtext=fontfile={SUBTITLE_FONT}:"
        f"text={escaped_text}:"
        f"fontcolor=white:"
        f"fontsize=60:"
        f"x=(w-text_w)/2:"
        f"y=h-text_h-100"
    )
    
    approaches = [
        ("Single quotes", filter_v1),
        ("Double quotes", filter_v2),
        ("No quotes", filter_v3),
    ]
    
    for approach_name, filter_expr in approaches:
        logger.info(f"\n--- Approach: {approach_name} ---")
        logger.info(f"Filter expression:\n{filter_expr}")
        
        # Build command
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
            f"{output_dir}/test_{test_name}_{approach_name.replace(' ', '_')}.mp4"
        ]
        
        logger.info(f"Command: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                logger.info(f"✓ SUCCESS: {approach_name}")
            else:
                logger.error(f"✗ FAILED: {approach_name}")
                logger.error(f"stderr: {result.stderr}")
        except Exception as e:
            logger.error(f"✗ EXCEPTION: {approach_name} - {e}")

if __name__ == "__main__":
    # Test case dari user
    test_subtitle = "Hei, ingat waktu itu aku pinjemin uang untuk [tujuan]? Aku butuh untuk [kebutuhanmu sekarang]."
    
    logger.info("Starting subtitle rendering tests...")
    test_drawtext_filter(test_subtitle, "main_test", "/tmp/ffmpeg_test")
    
    # Additional test cases
    simple_test = "Halo dunia"
    test_drawtext_filter(simple_test, "simple", "/tmp/ffmpeg_test")
    
    logger.info("\nAll tests completed!")
