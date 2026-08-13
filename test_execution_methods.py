#!/usr/bin/env python3
"""
Test: Bagaimana command dijalankan mempengaruhi hasil
- subprocess.run dengan list
- subprocess.run dengan shell=True
- os.system
- Melihat apakah ada perbedaan
"""

import logging
import tempfile
import subprocess
import os
from pathlib import Path
from PIL import Image
import shlex

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

def escape_text_for_ffmpeg(text: str) -> str:
    text = text.replace("\\", "\\\\")
    text = text.replace('"', '\\"')
    text = text.replace(":", "\\:")
    text = text.replace("[", "\\[")
    text = text.replace("]", "\\]")
    text = text.replace("%", "\\%")
    return text

def test_execution_method(method_name: str, cmd, subtitle_text: str):
    """Test berbagai cara menjalankan command"""
    
    logger.info(f"\n{'='*70}")
    logger.info(f"Execution Method: {method_name}")
    logger.info(f"{'='*70}")
    
    output_dir = "/tmp/ffmpeg_exec_method_test"
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    test_image = f"{output_dir}/test_image.png"
    output_video = f"{output_dir}/output_{method_name.replace(' ', '_')}.mp4"
    
    create_test_image(test_image)
    
    formatted = format_subtitle_text(subtitle_text)
    escaped = escape_text_for_ffmpeg(formatted)
    
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
    
    logger.info(f"Escaped text: {repr(escaped[:80])}...")
    
    try:
        if method_name == "subprocess.run (list)":
            cmd = [
                "ffmpeg", "-y", "-loop", "1", "-i", test_image,
                "-vf", filter_expr, "-t", "2",
                "-c:v", "libx264", "-pix_fmt", "yuv420p",
                "-preset", "ultrafast", "-crf", "28",
                output_video
            ]
            logger.info(f"Command list length: {len(cmd)}")
            logger.info(f"Filter arg (index 6): {repr(cmd[6][:80])}...")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            
        elif method_name == "subprocess.run (shell=True)":
            cmd_parts = [
                "ffmpeg", "-y", "-loop", "1", "-i", test_image,
                "-vf", filter_expr, "-t", "2",
                "-c:v", "libx264", "-pix_fmt", "yuv420p",
                "-preset", "ultrafast", "-crf", "28",
                output_video
            ]
            cmd_str = " ".join(shlex.quote(arg) for arg in cmd_parts)
            logger.info(f"Shell command: {cmd_str[:120]}...")
            result = subprocess.run(cmd_str, shell=True, capture_output=True, text=True, timeout=15)
        
        elif method_name == "os.system":
            cmd_parts = [
                "ffmpeg", "-y", "-loop", "1", "-i", test_image,
                "-vf", filter_expr, "-t", "2",
                "-c:v", "libx264", "-pix_fmt", "yuv420p",
                "-preset", "ultrafast", "-crf", "28",
                output_video
            ]
            cmd_str = " ".join(cmd_parts)
            logger.info(f"System command: {cmd_str[:120]}...")
            ret = os.system(cmd_str + " >/dev/null 2>&1")
            result = type('Result', (), {'returncode': ret >> 8 if ret != -1 else 1, 'stderr': ''})()
        
        if result.returncode == 0:
            logger.info(f"✓ SUCCESS")
            return True
        else:
            logger.error(f"✗ FAILED (return code: {result.returncode})")
            if hasattr(result, 'stderr') and "No such filter:" in result.stderr:
                for line in result.stderr.split('\n'):
                    if "No such filter:" in line:
                        logger.error(f"  Error: {line.strip()[:100]}")
            return False
    except Exception as e:
        logger.error(f"✗ EXCEPTION: {e}")
        return False

if __name__ == "__main__":
    subtitle = "Hei, ingat waktu itu aku pinjemin uang untuk [tujuan]? Aku butuh untuk [kebutuhanmu sekarang]."
    
    methods = [
        "subprocess.run (list)",
        "subprocess.run (shell=True)",
        "os.system",
    ]
    
    results = {}
    for method in methods:
        success = test_execution_method(method, None, subtitle)
        results[method] = success
    
    logger.info(f"\n{'='*70}")
    logger.info("SUMMARY")
    logger.info(f"{'='*70}")
    for method, success in results.items():
        status = "✓ PASS" if success else "✗ FAIL"
        logger.info(f"{status}: {method}")
