#!/usr/bin/env python3
"""
Test berbagai escaping strategies untuk FFmpeg drawtext
"""

import logging
import tempfile
import subprocess
from pathlib import Path
from PIL import Image

logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

OUTPUT_WIDTH = 1080
OUTPUT_HEIGHT = 1920
FPS = 30
SUBTITLE_FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

def create_test_image(output_path: str):
    img = Image.new('RGB', (OUTPUT_WIDTH, OUTPUT_HEIGHT), color=(73, 109, 137))
    img.save(output_path)

def format_subtitle_text(text: str) -> str:
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

def strategy_original(text: str) -> str:
    """Original escaping (current code)"""
    text = text.replace("\\", "\\\\")
    text = text.replace('"', '\\"')
    text = text.replace(":", "\\:")
    text = text.replace("[", "\\[")
    text = text.replace("]", "\\]")
    text = text.replace("%", "\\%")
    return text

def strategy_double_escape_brackets(text: str) -> str:
    """Double escape brackets for filter graph parsing"""
    text = text.replace("\\", "\\\\")
    text = text.replace('"', '\\"')
    text = text.replace(":", "\\:")
    text = text.replace("[", "\\\\[")  # Double escape
    text = text.replace("]", "\\\\]")  # Double escape
    text = text.replace("%", "\\%")
    return text

def strategy_no_escape_brackets(text: str) -> str:
    """Don't escape brackets, rely on single quotes"""
    text = text.replace("\\", "\\\\")
    text = text.replace('"', '\\"')
    text = text.replace(":", "\\:")
    # Don't escape [ and ]
    text = text.replace("%", "\\%")
    return text

def test_strategy(strategy_name: str, strategy_fn, subtitle_text: str):
    """Test a specific escaping strategy"""
    
    logger.info(f"\n{'='*70}")
    logger.info(f"Strategy: {strategy_name}")
    logger.info(f"{'='*70}")
    
    formatted = format_subtitle_text(subtitle_text)
    escaped = strategy_fn(formatted)
    
    logger.info(f"Original: {repr(subtitle_text)}")
    logger.info(f"Formatted: {repr(formatted)}")
    logger.info(f"Escaped: {repr(escaped)}")
    
    filter_expr = (
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
    
    logger.info(f"Filter: {repr(filter_expr[:150])}...")
    
    output_dir = "/tmp/ffmpeg_strategy_test"
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    test_image = f"{output_dir}/test_image.png"
    output_video = f"{output_dir}/output_{strategy_name.replace(' ', '_')}.mp4"
    
    create_test_image(test_image)
    
    cmd = [
        "ffmpeg", "-y", "-loop", "1", "-i", test_image,
        "-vf", filter_expr, "-t", "2",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-preset", "ultrafast", "-crf", "28",
        output_video
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        if result.returncode == 0:
            logger.info(f"✓ SUCCESS")
            return True
        else:
            logger.error(f"✗ FAILED")
            if "No such filter:" in result.stderr:
                for line in result.stderr.split('\n'):
                    if "No such filter:" in line:
                        logger.error(f"  Error: {line.strip()}")
            return False
    except Exception as e:
        logger.error(f"✗ EXCEPTION: {e}")
        return False

if __name__ == "__main__":
    subtitle = "Hei, ingat waktu itu aku pinjemin uang untuk [tujuan]? Aku butuh untuk [kebutuhanmu sekarang]."
    
    strategies = [
        ("Original (current)", strategy_original),
        ("Double escape brackets", strategy_double_escape_brackets),
        ("No escape brackets", strategy_no_escape_brackets),
    ]
    
    results = {}
    for name, fn in strategies:
        success = test_strategy(name, fn, subtitle)
        results[name] = success
    
    logger.info(f"\n{'='*70}")
    logger.info("SUMMARY")
    logger.info(f"{'='*70}")
    for name, success in results.items():
        status = "✓ PASS" if success else "✗ FAIL"
        logger.info(f"{status}: {name}")
