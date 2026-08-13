#!/usr/bin/env python3
"""
Verification test: Memastikan perbaikan escaping bekerja dengan berbagai karakter
"""

import logging
import tempfile
import subprocess
from pathlib import Path
from PIL import Image

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
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

def _escape_text_for_ffmpeg_new(text: str) -> str:
    """New version with single quote escaping"""
    text = text.replace("\\", "\\\\")
    text = text.replace(":", "\\:")
    text = text.replace("[", "\\[")
    text = text.replace("]", "\\]")
    text = text.replace("%", "\\%")
    text = text.replace("'", "\\'")
    return text

def test_subtitle(test_name: str, subtitle_text: str) -> bool:
    """Test a subtitle with various special characters"""
    
    logger.info(f"\n{'='*70}")
    logger.info(f"Test: {test_name}")
    logger.info(f"{'='*70}")
    
    formatted = _format_subtitle_text(subtitle_text)
    escaped = _escape_text_for_ffmpeg_new(formatted)
    
    logger.info(f"Original:  {repr(subtitle_text)}")
    logger.info(f"Formatted: {repr(formatted[:80])}{'...' if len(formatted) > 80 else ''}")
    logger.info(f"Escaped:   {repr(escaped[:80])}{'...' if len(escaped) > 80 else ''}")
    
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
    
    with tempfile.TemporaryDirectory() as temp_dir:
        test_image = f"{temp_dir}/test_image.png"
        output_video = f"{temp_dir}/output.mp4"
        
        create_test_image(test_image)
        
        cmd = [
            "ffmpeg", "-y", "-loop", "1", "-i", test_image,
            "-vf", filter_expr, "-t", "2",
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-preset", "ultrafast", "-crf", "28",
            output_video
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15, check=True)
            logger.info(f"✓ PASS")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"✗ FAIL")
            if "No such filter:" in e.stderr:
                for line in e.stderr.split('\n'):
                    if "No such filter:" in line:
                        logger.error(f"  {line.strip()[:100]}")
            else:
                logger.error(f"  {e.stderr[:200]}")
            return False

if __name__ == "__main__":
    test_cases = [
        ("User test case", "Hei, ingat waktu itu aku pinjemin uang untuk [tujuan]? Aku butuh untuk [kebutuhanmu sekarang]."),
        ("With single quotes", "Jangan bilang 'tidak bisa' karena [itu] bisa saja terjadi?"),
        ("With colons", "Jam 12:30 aku harus bayar [uang]: lima ratus ribu ya?"),
        ("With percent", "Diskon 50% untuk [semua] barang, beneran %?"),
        ("With backslash", "Jalur C:\\Users\\[temp] perlu di backup, setuju?"),
        ("With double quotes", 'Dia bilang "tidak" untuk [proposal] kami, ya?'),
        ("All special chars", "Test [all] 'chars' here: colon%, backslash\\, and \"quotes\"?"),
        ("Simple text", "Halo dunia ini adalah test sederhana."),
    ]
    
    results = {}
    for test_name, subtitle in test_cases:
        results[test_name] = test_subtitle(test_name, subtitle)
    
    logger.info(f"\n{'='*70}")
    logger.info("VERIFICATION SUMMARY")
    logger.info(f"{'='*70}")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, success in results.items():
        status = "✓ PASS" if success else "✗ FAIL"
        logger.info(f"{status}: {test_name}")
    
    logger.info(f"\nTotal: {passed}/{total} passed")
    
    if passed == total:
        logger.info("✓ All tests passed!")
    else:
        logger.error(f"✗ {total - passed} test(s) failed")
