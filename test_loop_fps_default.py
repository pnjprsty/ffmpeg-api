#!/usr/bin/env python3
"""
Test untuk memahami default FPS pada image loop dan bagaimana fps filter mempengaruhinya.
"""

import subprocess
import tempfile
import json
import os

def run_cmd(cmd):
    """Run command safely using list args"""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return 1, "", "Timeout"

def create_test_image():
    """Create a simple test image"""
    temp_dir = tempfile.mkdtemp()
    img_path = os.path.join(temp_dir, "test.png")
    
    # Create using ffmpeg
    cmd = ["ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=red:s=1080x1920:d=1", 
           "-frames:v", "1", img_path]
    returncode, _, _ = run_cmd(cmd)
    
    if returncode == 0:
        return img_path, temp_dir
    return None, temp_dir

def test_loop_default_fps():
    """Test default FPS ketika menggunakan -loop 1"""
    
    print("\n" + "="*80)
    print("TEST 1: Default FPS pada -loop 1 tanpa explicit fps filter")
    print("="*80)
    
    img_path, temp_dir = create_test_image()
    if not img_path:
        print("Failed to create test image")
        return
    
    output = os.path.join(temp_dir, "loop_default.mp4")
    
    # Use list args to avoid shell escaping issues
    cmd = ["ffmpeg", "-y", "-loop", "1", "-i", img_path, 
           "-t", "5", "-c:v", "libx264", "-pix_fmt", "yuv420p", output]
    
    print(f"Command: {' '.join(cmd)}")
    
    returncode, stdout, stderr = run_cmd(cmd)
    
    if returncode != 0:
        print(f"FFmpeg failed: {stderr[:500]}")
        return
    
    # Analyze
    print("\nAnalyzing output...")
    info_cmd = ["ffprobe", "-v", "error", "-select_streams", "v:0", 
                "-show_entries", "stream=r_frame_rate,nb_frames,duration", 
                "-of", "default=nokey=1:noprint_wrappers=1", output]
    
    returncode, stdout, stderr = run_cmd(info_cmd)
    
    if returncode == 0:
        lines = stdout.strip().split('\n')
        print(f"r_frame_rate: {lines[0] if len(lines) > 0 else 'N/A'}")
        print(f"nb_frames: {lines[1] if len(lines) > 1 else 'N/A'}")
        print(f"duration: {lines[2] if len(lines) > 2 else 'N/A'}")

def test_loop_with_explicit_fps():
    """Test -loop 1 dengan explicit fps filter"""
    
    print("\n" + "="*80)
    print("TEST 2: -loop 1 + fps=30 filter")
    print("="*80)
    
    img_path, temp_dir = create_test_image()
    if not img_path:
        print("Failed to create test image")
        return
    
    output = os.path.join(temp_dir, "loop_fps30.mp4")
    
    cmd = ["ffmpeg", "-y", "-loop", "1", "-i", img_path, 
           "-vf", "fps=30",
           "-t", "5", "-c:v", "libx264", "-pix_fmt", "yuv420p", output]
    
    print(f"Command: {' '.join(cmd)}")
    
    returncode, stdout, stderr = run_cmd(cmd)
    
    if returncode != 0:
        print(f"FFmpeg failed: {stderr[:500]}")
        return
    
    print("\nAnalyzing output...")
    info_cmd = ["ffprobe", "-v", "error", "-select_streams", "v:0", 
                "-show_entries", "stream=r_frame_rate,nb_frames,duration", 
                "-of", "default=nokey=1:noprint_wrappers=1", output]
    
    returncode, stdout, stderr = run_cmd(info_cmd)
    
    if returncode == 0:
        lines = stdout.strip().split('\n')
        print(f"r_frame_rate: {lines[0] if len(lines) > 0 else 'N/A'}")
        print(f"nb_frames: {lines[1] if len(lines) > 1 else 'N/A'}")
        print(f"duration: {lines[2] if len(lines) > 2 else 'N/A'}")

def test_loop_with_framerate_option():
    """Test -loop 1 dengan -framerate option sebelum -i"""
    
    print("\n" + "="*80)
    print("TEST 3: -framerate 30 -loop 1 -i (explicit input framerate)")
    print("="*80)
    
    img_path, temp_dir = create_test_image()
    if not img_path:
        print("Failed to create test image")
        return
    
    output = os.path.join(temp_dir, "loop_framerate30.mp4")
    
    cmd = ["ffmpeg", "-y", "-framerate", "30", "-loop", "1", "-i", img_path, 
           "-t", "5", "-c:v", "libx264", "-pix_fmt", "yuv420p", output]
    
    print(f"Command: {' '.join(cmd)}")
    
    returncode, stdout, stderr = run_cmd(cmd)
    
    if returncode != 0:
        print(f"FFmpeg failed: {stderr[:500]}")
        return
    
    print("\nAnalyzing output...")
    info_cmd = ["ffprobe", "-v", "error", "-select_streams", "v:0", 
                "-show_entries", "stream=r_frame_rate,nb_frames,duration", 
                "-of", "default=nokey=1:noprint_wrappers=1", output]
    
    returncode, stdout, stderr = run_cmd(info_cmd)
    
    if returncode == 0:
        lines = stdout.strip().split('\n')
        print(f"r_frame_rate: {lines[0] if len(lines) > 0 else 'N/A'}")
        print(f"nb_frames: {lines[1] if len(lines) > 1 else 'N/A'}")
        print(f"duration: {lines[2] if len(lines) > 2 else 'N/A'}")

def test_loop_with_r_option():
    """Test -loop 1 dengan -r option untuk output framerate"""
    
    print("\n" + "="*80)
    print("TEST 4: -loop 1 -i ... -r 30 (output framerate)")
    print("="*80)
    
    img_path, temp_dir = create_test_image()
    if not img_path:
        print("Failed to create test image")
        return
    
    output = os.path.join(temp_dir, "loop_r30.mp4")
    
    cmd = ["ffmpeg", "-y", "-loop", "1", "-i", img_path, 
           "-r", "30",
           "-t", "5", "-c:v", "libx264", "-pix_fmt", "yuv420p", output]
    
    print(f"Command: {' '.join(cmd)}")
    
    returncode, stdout, stderr = run_cmd(cmd)
    
    if returncode != 0:
        print(f"FFmpeg failed: {stderr[:500]}")
        return
    
    print("\nAnalyzing output...")
    info_cmd = ["ffprobe", "-v", "error", "-select_streams", "v:0", 
                "-show_entries", "stream=r_frame_rate,nb_frames,duration", 
                "-of", "default=nokey=1:noprint_wrappers=1", output]
    
    returncode, stdout, stderr = run_cmd(info_cmd)
    
    if returncode == 0:
        lines = stdout.strip().split('\n')
        print(f"r_frame_rate: {lines[0] if len(lines) > 0 else 'N/A'}")
        print(f"nb_frames: {lines[1] if len(lines) > 1 else 'N/A'}")
        print(f"duration: {lines[2] if len(lines) > 2 else 'N/A'}")

def main():
    test_loop_default_fps()
    test_loop_with_explicit_fps()
    test_loop_with_framerate_option()
    test_loop_with_r_option()
    
    print("\n\n" + "="*80)
    print("SUMMARY & FINDINGS")
    print("="*80)
    print("""
Expected findings:

1. -loop 1 tanpa fps filter: Kemungkinan output 25fps (default)
   - Ini BISA menjadi root cause!

2. -loop 1 + fps=30: Output 30fps
   - fps filter harus berhasil convert ke 30fps

3. -framerate 30 -loop 1: Output 30fps
   - Explicit framerate option pada input

4. -loop 1 + -r 30: Output 30fps
   - Explicit framerate option pada output

Jika Test 1 menunjukkan 25fps, maka root cause sudah ketemu:
- app/renderer.py tidak set input framerate sebelum -loop 1
- Akibatnya input default ke 25fps
- fps filter di filtergraph tidak cukup untuk fix frame count
- Audio menjadi lebih pendek karena frame count tidak sesuai
    """)

if __name__ == "__main__":
    main()
