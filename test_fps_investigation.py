#!/usr/bin/env python3
"""
Test untuk memeriksa _create_scene_video() dan verifikasi FPS issue.

Focus:
1. Apakah fps filter atau scale filter mengubah FPS dari 30 menjadi 25?
2. Berapa banyak frame yang actually dihasilkan?
3. Apakah -t duration flag berhasil mengontrol durasi output?
"""

import subprocess
import tempfile
import json
import os
from pathlib import Path

def run_cmd(cmd):
    """Run command and return output"""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
    return result.returncode, result.stdout, result.stderr

def create_test_image():
    """Create a simple test image"""
    temp_dir = tempfile.mkdtemp()
    img_path = os.path.join(temp_dir, "test.png")
    
    # Create a simple 1080x1920 image using ImageMagick or ffmpeg
    cmd = f"ffmpeg -y -f lavfi -i color=c=red:s=1080x1920:d=1 -frames:v 1 {img_path}"
    returncode, _, _ = run_cmd(cmd)
    
    if returncode == 0:
        return img_path, temp_dir
    return None, temp_dir

def test_create_scene_video_with_fps_30():
    """
    Test creating scene video menggunakan exact code dari app/renderer.py
    dengan FPS = 30 dan duration = 11.556s
    """
    
    print("\n" + "="*80)
    print("TEST 1: Creating scene video dengan FPS=30, duration=11.556s")
    print("="*80)
    
    img_path, temp_dir = create_test_image()
    if not img_path:
        print("Failed to create test image")
        return
    
    OUTPUT_WIDTH = 1080
    OUTPUT_HEIGHT = 1920
    FPS = 30
    duration = 11.556
    
    output_path = os.path.join(temp_dir, "scene_test_fps30.mp4")
    
    # Exact filter dari app/renderer.py line 265-284
    font_filter = (
        f"scale={OUTPUT_WIDTH}:{OUTPUT_HEIGHT}:force_original_aspect_ratio=decrease,"
        f"pad={OUTPUT_WIDTH}:{OUTPUT_HEIGHT}:(ow-iw)/2:(oh-ih)/2:color=black,"
        f"fps={FPS},"
        f"drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:"
        f"text='Test':"
        f"fontcolor=white:"
        f"fontsize=60:"
        f"borderw=3:"
        f"bordercolor=black"
    )
    
    cmd = [
        "ffmpeg",
        "-y",
        "-loop", "1",
        "-i", img_path,
        "-vf", font_filter,
        "-t", str(duration),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-preset", "medium",
        "-crf", "23",
        output_path
    ]
    
    print(f"\nCommand: {' '.join(cmd)}")
    print(f"\nFilter: {font_filter}")
    
    returncode, stdout, stderr = run_cmd(" ".join(cmd))
    
    if returncode != 0:
        print(f"\nFFmpeg failed: {stderr}")
        return
    
    # Analyze output
    print(f"\nOutput created: {output_path}")
    
    ffprobe_cmd = f'ffprobe -v error -show_format -show_streams -of json "{output_path}"'
    returncode, stdout, stderr = run_cmd(ffprobe_cmd)
    
    if returncode == 0:
        try:
            info = json.loads(stdout)
            fmt = info.get('format', {})
            streams = info.get('streams', [])
            
            print(f"\nFormat info:")
            print(f"  Duration: {fmt.get('duration', 'N/A')}s")
            
            for stream in streams:
                if stream.get('codec_type') == 'video':
                    print(f"\nVideo stream:")
                    print(f"  Codec: {stream.get('codec_name', 'N/A')}")
                    print(f"  Resolution: {stream.get('width', 'N/A')}x{stream.get('height', 'N/A')}")
                    print(f"  FPS (r_frame_rate): {stream.get('r_frame_rate', 'N/A')}")
                    print(f"  Duration: {stream.get('duration', 'N/A')}s")
                    print(f"  Nb frames: {stream.get('nb_frames', 'N/A')}")
                    
                    # Calculate expected vs actual
                    try:
                        fps_str = stream.get('r_frame_rate', '30/1')
                        if '/' in fps_str:
                            num, den = map(float, fps_str.split('/'))
                            actual_fps = num / den
                        else:
                            actual_fps = float(fps_str)
                        
                        nb_frames = int(stream.get('nb_frames', 0))
                        actual_duration = nb_frames / actual_fps if actual_fps > 0 else 0
                        
                        print(f"\nCalculations:")
                        print(f"  Actual FPS: {actual_fps}")
                        print(f"  Actual frames: {nb_frames}")
                        print(f"  Calculated duration: {actual_duration:.6f}s")
                        print(f"  Expected duration: {duration:.6f}s")
                        print(f"  Expected frames @ {actual_fps}fps: {duration * actual_fps:.2f}")
                        print(f"  Difference: {actual_duration - duration:.6f}s")
                    except Exception as e:
                        print(f"  Calculation error: {e}")
        except json.JSONDecodeError:
            print("Failed to parse ffprobe output")
    
    # Cleanup
    import shutil
    shutil.rmtree(temp_dir)

def test_fps_filter_behavior():
    """
    Test bagaimana fps filter mempengaruhi output ketika input adalah image loop.
    
    Hypothesis: fps filter mungkin menggunakan default frame rate dari color/image source.
    """
    
    print("\n\n" + "="*80)
    print("TEST 2: FPS filter behavior on image loop")
    print("="*80)
    
    temp_dir = tempfile.mkdtemp()
    output_path = os.path.join(temp_dir, "fps_test.mp4")
    
    img_path, _ = create_test_image()
    if not img_path:
        print("Failed to create test image")
        return
    
    # Test dengan berbagai fps values
    fps_values = [25, 30, 24, 60]
    
    for fps in fps_values:
        output = os.path.join(temp_dir, f"fps_test_{fps}.mp4")
        
        # Simple filter dengan hanya fps
        cmd = (
            f"ffmpeg -y -loop 1 -i {img_path} "
            f"-vf 'fps={fps}' "
            f"-t 5 "
            f"-c:v libx264 -pix_fmt yuv420p {output}"
        )
        
        returncode, _, _ = run_cmd(cmd)
        
        if returncode == 0:
            ffprobe_cmd = f'ffprobe -v error -select_streams v:0 -show_entries stream=r_frame_rate,nb_frames -of default=nokey=1:noprint_wrappers=1 "{output}"'
            returncode, stdout, stderr = run_cmd(ffprobe_cmd)
            
            if returncode == 0:
                lines = stdout.strip().split('\n')
                if len(lines) >= 2:
                    actual_fps = lines[0]
                    frames = lines[1]
                    print(f"\nFPS={fps} -> Output: {actual_fps} fps, {frames} frames")

def main():
    test_create_scene_video_with_fps_30()
    test_fps_filter_behavior()
    
    print("\n\n" + "="*80)
    print("ANALISIS HASIL TEST")
    print("="*80)
    print("""
Kemungkinan masalah:

1. Image loop `-loop 1` menggunakan default FPS
   - Saat `-loop 1` tanpa `-framerate` explicit, FFmpeg mungkin menggunakan default (25fps?)
   - Ini bisa explain kenapa output hanya 25fps bukan 30fps

2. FPS filter mungkin tidak override frame rate correctly
   - Jika input sudah 25fps, fps filter mungkin tidak berubah
   - Atau fps filter bisa menggunakan frame rate dari preceding filter

3. Pada line 268 di app/renderer.py:
   `f"fps={FPS},"`
   
   Ini seharusnya ensure output adalah 30fps, TETAPI:
   - ffmpeg color source atau loop mungkin menggunakan 25fps default
   - fps filter mungkin hanya drop/duplicate frame, bukan regenerate

4. Scale + pad filters mungkin juga mempengaruhi FPS
   
SOLUSI UNTUK DICEK:
- Tambahkan `-framerate 30` sebelum `-i` untuk specify input framerate
- Atau gunakan `-r 30` untuk force output framerate
- Verify bahwa fps filter dalam filtergraph benar-benar menghasilkan 30fps
    """)

if __name__ == "__main__":
    main()
