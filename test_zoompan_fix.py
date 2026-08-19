#!/usr/bin/env python3
"""
Test zoompan fix with frame-based interpolation instead of timestamp-based.
Verifies that the Ken Burns effect works correctly without FFmpeg errors.
"""

import sys
import tempfile
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw

def create_dummy_image(width: int, height: int, filepath: str) -> None:
    """Create a simple test image with gradient"""
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)
    
    # Draw gradient-like pattern
    for i in range(0, height, 20):
        color = (100 + (i % 156), 150, 200)
        draw.rectangle([0, i, width, i + 20], fill=color)
    
    # Add text label
    try:
        draw.text((50, 50), "Test Image", fill='black')
    except:
        pass
    
    img.save(filepath)
    print(f"Created test image: {filepath}")

def test_zoompan_expression(duration: float, fps: int = 30) -> None:
    """
    Test zoompan filter expression with frame-based interpolation
    
    Args:
        duration: Scene duration in seconds (with precision, e.g., 7.416)
        fps: Frames per second
    """
    print(f"\n=== Testing zoompan with duration={duration}s, fps={fps} ===")
    
    # Calculate frame count for Ken Burns
    frame_count = duration * fps
    print(f"Frame count: {frame_count}")
    
    # Ken Burns parameters
    zoom_start = 1.0
    zoom_end = 1.05
    pan_x = 0.0
    pan_y = 0.02
    output_width = 1080
    output_height = 1920
    
    # Generate expression (mimicking what renderer.py does)
    zoom_expr = f"zoom+({zoom_end}-{zoom_start})*on/{frame_count}"
    x_expr = f"iw/2-(iw/zoom/2)+{pan_x}*on/{fps}/{duration}"
    y_expr = f"ih/2-(ih/zoom/2)+{pan_y}*on/{fps}/{duration}"
    
    print(f"\nZoompan expressions:")
    print(f"  zoom: {zoom_expr}")
    print(f"  x:    {x_expr}")
    print(f"  y:    {y_expr}")
    
    # Create temporary directory and files
    with tempfile.TemporaryDirectory(prefix="test_zoompan_") as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Create test image
        test_image = tmpdir / "test.jpg"
        create_dummy_image(1920, 1080, str(test_image))
        
        # Create output file
        output_video = tmpdir / "output.mp4"
        
        # Build FFmpeg command with new zoompan expressions
        font_filter = (
            f"scale={output_width}:{output_height}:force_original_aspect_ratio=decrease,"
            f"pad={output_width}:{output_height}:(ow-iw)/2:(oh-ih)/2:color=black,"
            f"zoompan=z='{zoom_expr}':"
            f"x='{x_expr}':"
            f"y='{y_expr}':"
            f"s={output_width}x{output_height},"
            f"fps={fps}"
        )
        
        cmd = [
            "ffmpeg",
            "-y",
            "-loop", "1",
            "-i", str(test_image),
            "-vf", font_filter,
            "-t", str(duration),
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-preset", "fast",
            "-crf", "28",
            str(output_video)
        ]
        
        print(f"\nFilter expression:\n  {repr(font_filter)}\n")
        print(f"Running FFmpeg command...")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                print(f"✓ SUCCESS: Video created at {output_video}")
                if output_video.exists():
                    size = output_video.stat().st_size
                    print(f"  File size: {size / 1024 / 1024:.2f} MB")
                return True
            else:
                print(f"✗ FAILED: FFmpeg returned code {result.returncode}")
                if "Undefined constant or missing '('" in result.stderr:
                    print(f"  ERROR: Still getting zoompan expression parsing error!")
                    print(f"  stderr: {result.stderr[-500:]}")
                else:
                    print(f"  stderr: {result.stderr[-500:]}")
                return False
                
        except subprocess.TimeoutExpired:
            print(f"✗ TIMEOUT: FFmpeg took too long")
            return False
        except Exception as e:
            print(f"✗ ERROR: {e}")
            return False

if __name__ == "__main__":
    print("Testing zoompan frame-based interpolation fix\n")
    
    # Test cases with different durations
    test_cases = [
        7.416,      # Original error duration
        5.0,        # Simple case
        10.5,       # Non-integer
        3.333,      # Repeating decimal
    ]
    
    results = []
    for duration in test_cases:
        success = test_zoompan_expression(duration)
        results.append((duration, success))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for duration, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status}: duration={duration}s")
    
    all_passed = all(success for _, success in results)
    sys.exit(0 if all_passed else 1)
