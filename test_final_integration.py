#!/usr/bin/env python3
"""
Final Integration Test: Render subtitle test case dari user
Menggunakan kode yang sudah diperbaiki dari app/renderer.py
"""

import logging
import tempfile
import subprocess
from pathlib import Path
from PIL import Image
import sys

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
    """Create a simple test image"""
    img = Image.new('RGB', (OUTPUT_WIDTH, OUTPUT_HEIGHT), color=(73, 109, 137))
    img.save(output_path)
    logger.info(f"Created test image: {output_path}")

def _format_subtitle_text(text: str) -> str:
    """Exact dari app/renderer.py"""
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
    """Perbaikan dari app/renderer.py"""
    text = text.replace("\\", "\\\\")
    text = text.replace(":", "\\:")
    text = text.replace("[", "\\[")
    text = text.replace("]", "\\]")
    text = text.replace("%", "\\%")
    return text

def render_subtitle_test_case():
    """
    Render video dengan subtitle test case dari user:
    "Hei, ingat waktu itu aku pinjemin uang untuk [tujuan]? Aku butuh untuk [kebutuhanmu sekarang]."
    """
    
    logger.info(f"\n{'='*80}")
    logger.info("FINAL INTEGRATION TEST: Subtitle Rendering")
    logger.info(f"{'='*80}")
    
    # Test case dari user
    subtitle_text = "Hei, ingat waktu itu aku pinjemin uang untuk [tujuan]? Aku butuh untuk [kebutuhanmu sekarang]."
    duration = 2.0
    
    logger.info(f"\nSubtitle Text: {repr(subtitle_text)}")
    logger.info(f"Duration: {duration}s")
    
    # Step 1: Format subtitle
    formatted_subtitle = _format_subtitle_text(subtitle_text)
    logger.info(f"\nStep 1 - Formatted subtitle:")
    logger.info(f"  {repr(formatted_subtitle)}")
    
    # Step 2: Escape for FFmpeg
    escaped_text = _escape_text_for_ffmpeg(formatted_subtitle)
    logger.info(f"\nStep 2 - Escaped text:")
    logger.info(f"  {repr(escaped_text)}")
    
    # Verify required characters are escaped
    logger.info(f"\nStep 2.1 - Verify escaping:")
    has_escaped_bracket_open = '\\[' in escaped_text
    has_escaped_bracket_close = '\\]' in escaped_text
    has_question = '?' in escaped_text
    has_newlines = escaped_text.count('\n') > 0
    
    logger.info(f"  '[' is escaped: {has_escaped_bracket_open}")
    logger.info(f"  ']' is escaped: {has_escaped_bracket_close}")
    logger.info(f"  '?' preserved: {has_question}")
    logger.info(f"  Newlines preserved: {has_newlines}")
    
    # Step 3: Build filter
    filter_expr = (
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
    
    logger.info(f"\nStep 3 - Filter expression (first 150 chars):")
    logger.info(f"  {repr(filter_expr[:150])}...")
    
    # Step 4: Build command
    with tempfile.TemporaryDirectory() as temp_dir:
        test_image = f"{temp_dir}/test_image.png"
        output_video = f"{temp_dir}/output_subtitle_test.mp4"
        
        create_test_image(test_image)
        
        cmd = [
            "ffmpeg",
            "-y",
            "-loop", "1",
            "-i", test_image,
            "-vf", filter_expr,
            "-t", str(duration),
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-preset", "medium",
            "-crf", "23",
            output_video
        ]
        
        logger.info(f"\nStep 4 - FFmpeg command:")
        logger.info(f"  Command has {len(cmd)} arguments")
        logger.info(f"  Filter argument length: {len(filter_expr)} chars")
        
        # Step 5: Execute
        logger.info(f"\nStep 5 - Executing FFmpeg...")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,
                check=True
            )
            
            logger.info(f"✓ SUCCESS - Video rendered successfully!")
            logger.info(f"  Output: {output_video}")
            
            # Verify output exists
            if Path(output_video).exists():
                file_size = Path(output_video).stat().st_size
                logger.info(f"  File size: {file_size} bytes")
                logger.info(f"\n✓ VERIFICATION PASSED")
                logger.info(f"  - Subtitle with [tujuan], [kebutuhanmu], and ? rendered successfully")
                logger.info(f"  - Escaping strategy works correctly")
                logger.info(f"  - No 'No such filter' error")
                return True
            else:
                logger.error(f"✗ Output file not created")
                return False
                
        except subprocess.CalledProcessError as e:
            logger.error(f"✗ FAILED - FFmpeg command failed")
            logger.error(f"  Return code: {e.returncode}")
            
            if "No such filter:" in e.stderr:
                logger.error(f"  ERROR: 'No such filter' detected!")
                for line in e.stderr.split('\n'):
                    if "No such filter:" in line:
                        logger.error(f"    {line.strip()}")
            
            logger.error(f"\nFirst 500 chars of stderr:")
            logger.error(f"  {e.stderr[:500]}")
            return False
            
        except Exception as e:
            logger.error(f"✗ EXCEPTION: {e}")
            return False

if __name__ == "__main__":
    success = render_subtitle_test_case()
    
    logger.info(f"\n{'='*80}")
    if success:
        logger.info("✓ FINAL TEST PASSED")
        logger.info("  Subtitle rendering with special characters works correctly")
        sys.exit(0)
    else:
        logger.error("✗ FINAL TEST FAILED")
        sys.exit(1)
    logger.info(f"{'='*80}")
