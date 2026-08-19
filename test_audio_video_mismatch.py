#!/usr/bin/env python3
"""
Test script untuk investigasi mismatch audio-video pada final output dengan 11 scene.

Tujuan:
1. Generate dummy audio files dengan durasi spesifik sesuai data log
2. Generate dummy video dengan durasi spesifik
3. Render final video dengan 11 scene
4. Analisis timeline menggunakan ffprobe
"""

import subprocess
import os
import sys
import tempfile
import logging
from pathlib import Path
import json

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Scene durations dari log yang dilaporkan user
# Scene 10 (index 9): 11.556s
# Scene 11 (index 10): 12.888s
# Total untuk 11 scene: 141.624s

# Saya perlu mencari distribusi yang totalnya 141.624s
# Asumsikan 9 scene pertama total = 141.624 - (11.556 + 12.888) = 117.18s
# Rata-rata per scene ~13.02s

SCENE_DURATIONS = [
    13.02, 13.02, 13.02, 13.02, 13.02, 13.02, 13.02, 13.02, 13.02,
    11.556,  # Scene 10 (index 9)
    12.888   # Scene 11 (index 10)
]

# Adjust untuk total 141.624s
total = sum(SCENE_DURATIONS)
logger.info(f"Total durations: {total:.3f}s")
logger.info(f"Target total: 141.624s")
logger.info(f"Difference: {total - 141.624:.3f}s")

# Adjust scene pertama untuk mencapai total tepat
SCENE_DURATIONS[0] -= (total - 141.624)
total = sum(SCENE_DURATIONS)
logger.info(f"Adjusted total: {total:.6f}s")

assert len(SCENE_DURATIONS) == 11

def run_command(cmd, timeout=60):
    """Run shell command and return output"""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        logger.error(f"Command timed out: {cmd}")
        return 1, "", "Timeout"

def create_dummy_audio(duration, sample_rate=44100, output_path=None):
    """Create dummy audio file with specified duration"""
    if output_path is None:
        output_path = tempfile.NamedTemporaryFile(suffix='.aac', delete=False).name
    
    # Create silent audio using FFmpeg with AAC codec
    cmd = f"ffmpeg -y -f lavfi -i anullsrc=r={sample_rate}:cl=mono -t {duration} -c:a aac -b:a 192k {output_path}"
    returncode, stdout, stderr = run_command(cmd, timeout=30)
    
    if returncode != 0:
        logger.error(f"Failed to create audio: {stderr}")
        return None
    
    logger.info(f"Created audio: {output_path} (duration: {duration}s)")
    return output_path

def create_dummy_video(duration, output_path=None):
    """Create dummy video file with specified duration"""
    if output_path is None:
        output_path = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False).name
    
    # Create video from solid color
    cmd = f"ffmpeg -y -f lavfi -i color=c=blue:s=1080x1920:d={duration} -pix_fmt yuv420p {output_path}"
    returncode, stdout, stderr = run_command(cmd, timeout=60)
    
    if returncode != 0:
        logger.error(f"Failed to create video: {stderr}")
        return None
    
    logger.info(f"Created video: {output_path} (duration: {duration}s)")
    return output_path

def get_ffprobe_info(file_path):
    """Get detailed info from ffprobe"""
    cmd = f'ffprobe -v error -show_format -show_streams -of json "{file_path}"'
    returncode, stdout, stderr = run_command(cmd)
    
    if returncode != 0:
        logger.error(f"ffprobe failed: {stderr}")
        return None
    
    try:
        return json.loads(stdout)
    except json.JSONDecodeError:
        logger.error("Failed to parse ffprobe JSON output")
        return None

def analyze_video(file_path):
    """Detailed analysis of video file"""
    logger.info(f"\n{'='*80}")
    logger.info(f"ANALYZING: {Path(file_path).name}")
    logger.info(f"{'='*80}")
    
    # Get ffprobe info
    info = get_ffprobe_info(file_path)
    if not info:
        return None
    
    result = {
        'file': Path(file_path).name,
        'format': info.get('format', {}),
        'streams': info.get('streams', [])
    }
    
    # Log format info
    fmt = result['format']
    logger.info(f"Duration: {fmt.get('duration', 'N/A')}s")
    logger.info(f"Bitrate: {fmt.get('bit_rate', 'N/A')} bps")
    
    # Log stream info
    for i, stream in enumerate(result['streams']):
        logger.info(f"\nStream {i}: {stream.get('codec_type', 'unknown')}")
        
        if stream.get('codec_type') == 'video':
            logger.info(f"  Codec: {stream.get('codec_name', 'N/A')}")
            logger.info(f"  Resolution: {stream.get('width', 'N/A')}x{stream.get('height', 'N/A')}")
            logger.info(f"  FPS: {stream.get('r_frame_rate', 'N/A')}")
            logger.info(f"  Duration: {stream.get('duration', 'N/A')}s")
            logger.info(f"  Nb frames: {stream.get('nb_frames', 'N/A')}")
            logger.info(f"  Start time: {stream.get('start_time', 'N/A')}s")
            
        elif stream.get('codec_type') == 'audio':
            logger.info(f"  Codec: {stream.get('codec_name', 'N/A')}")
            logger.info(f"  Sample rate: {stream.get('sample_rate', 'N/A')}")
            logger.info(f"  Channels: {stream.get('channels', 'N/A')}")
            logger.info(f"  Duration: {stream.get('duration', 'N/A')}s")
            logger.info(f"  Start time: {stream.get('start_time', 'N/A')}s")
    
    return result

def main():
    """Main test workflow"""
    logger.info(f"Starting audio-video mismatch investigation")
    logger.info(f"Total scenes: {len(SCENE_DURATIONS)}")
    logger.info(f"Total duration: {sum(SCENE_DURATIONS):.6f}s")
    logger.info(f"Scene 10 (index 9): {SCENE_DURATIONS[9]}s")
    logger.info(f"Scene 11 (index 10): {SCENE_DURATIONS[10]}s")
    
    # Create temporary directory
    temp_dir = tempfile.mkdtemp(prefix="audio_video_test_")
    logger.info(f"\nTemp directory: {temp_dir}")
    
    # Create audio files
    logger.info(f"\n{'='*80}")
    logger.info("STEP 1: Creating audio files")
    logger.info(f"{'='*80}")
    
    audio_files = []
    for i, duration in enumerate(SCENE_DURATIONS):
        audio_path = os.path.join(temp_dir, f"audio_{i:02d}.aac")
        audio_file = create_dummy_audio(duration, output_path=audio_path)
        if audio_file:
            audio_files.append(audio_file)
        else:
            logger.error(f"Failed to create audio {i}")
            return
    
    # Create video files
    logger.info(f"\n{'='*80}")
    logger.info("STEP 2: Creating video files")
    logger.info(f"{'='*80}")
    
    video_files = []
    for i, duration in enumerate(SCENE_DURATIONS):
        video_path = os.path.join(temp_dir, f"video_{i:02d}.mp4")
        video_file = create_dummy_video(duration, output_path=video_path)
        if video_file:
            video_files.append(video_file)
        else:
            logger.error(f"Failed to create video {i}")
            return
    
    # Analyze Scene 10 and Scene 11 videos
    logger.info(f"\n{'='*80}")
    logger.info("STEP 3: Detailed analysis of Scene 10 and Scene 11")
    logger.info(f"{'='*80}")
    
    analyze_video(video_files[9])  # Scene 10
    analyze_video(video_files[10])  # Scene 11
    
    # Analyze Scene 10 and 11 audio
    logger.info(f"\n{'='*80}")
    logger.info("STEP 4: Audio analysis")
    logger.info(f"{'='*80}")
    
    # Get durations from ffprobe
    audio_durations = []
    video_durations = []
    
    for i in [9, 10]:  # Scene 10 and 11
        audio_info = get_ffprobe_info(audio_files[i])
        video_info = get_ffprobe_info(video_files[i])
        
        if audio_info and video_info:
            audio_dur = float(audio_info['format'].get('duration', 0))
            video_dur = float(video_info['format'].get('duration', 0))
            
            audio_durations.append(audio_dur)
            video_durations.append(video_dur)
            
            logger.info(f"\nScene {i+1}:")
            logger.info(f"  Expected duration: {SCENE_DURATIONS[i]:.6f}s")
            logger.info(f"  Audio actual duration: {audio_dur:.6f}s")
            logger.info(f"  Video actual duration: {video_dur:.6f}s")
            logger.info(f"  Audio vs Video difference: {abs(audio_dur - video_dur):.6f}s")
    
    # Timeline analysis
    logger.info(f"\n{'='*80}")
    logger.info("STEP 5: Timeline analysis for mismatch")
    logger.info(f"{'='*80}")
    
    # Calculate when Scene 10 ends and Scene 11 starts in expected timeline
    scenes_0_9_duration = sum(SCENE_DURATIONS[:10])
    scene_10_end_expected = scenes_0_9_duration
    scene_11_start_expected = scenes_0_9_duration  # No gap
    
    logger.info(f"\nExpected timeline:")
    logger.info(f"  Scene 10 (index 9) duration: {SCENE_DURATIONS[9]:.6f}s")
    logger.info(f"  Scene 11 (index 10) duration: {SCENE_DURATIONS[10]:.6f}s")
    logger.info(f"  Sum of scenes 0-9: {scenes_0_9_duration:.6f}s")
    logger.info(f"  Scene 10 should end at: {scene_10_end_expected:.6f}s")
    logger.info(f"  Scene 11 should start at: {scene_11_start_expected:.6f}s")
    
    if audio_durations and video_durations:
        logger.info(f"\nActual vs Expected:")
        logger.info(f"  Scene 10 audio: {audio_durations[0]:.6f}s (expected {SCENE_DURATIONS[9]:.6f}s, diff: {audio_durations[0] - SCENE_DURATIONS[9]:.6f}s)")
        logger.info(f"  Scene 10 video: {video_durations[0]:.6f}s (expected {SCENE_DURATIONS[9]:.6f}s, diff: {video_durations[0] - SCENE_DURATIONS[9]:.6f}s)")
        logger.info(f"  Scene 11 audio: {audio_durations[1]:.6f}s (expected {SCENE_DURATIONS[10]:.6f}s, diff: {audio_durations[1] - SCENE_DURATIONS[10]:.6f}s)")
        logger.info(f"  Scene 11 video: {video_durations[1]:.6f}s (expected {SCENE_DURATIONS[10]:.6f}s, diff: {video_durations[1] - SCENE_DURATIONS[10]:.6f}s)")
    
    # Additional frame analysis
    logger.info(f"\n{'='*80}")
    logger.info("STEP 6: Frame analysis for video")
    logger.info(f"{'='*80}")
    
    for i in [9, 10]:
        cmd = f"ffprobe -v error -select_streams v:0 -count_frames -show_entries stream=nb_read_frames -of default=nokey=1:noprint_wrappers=1 {video_files[i]}"
        returncode, stdout, stderr = run_command(cmd)
        if returncode == 0:
            frames = stdout.strip()
            expected_frames = SCENE_DURATIONS[i] * 30  # Assuming 30 FPS
            logger.info(f"Scene {i+1}:")
            logger.info(f"  Frames from ffprobe: {frames}")
            logger.info(f"  Expected frames (duration * FPS): {expected_frames:.2f}")
    
    logger.info(f"\n{'='*80}")
    logger.info("Investigation complete. Temp files kept in:")
    logger.info(f"  {temp_dir}")
    logger.info(f"{'='*80}")
    
    print(f"\nFile paths for manual inspection:")
    print(f"Scene 10 video: {video_files[9]}")
    print(f"Scene 11 video: {video_files[10]}")
    print(f"Scene 10 audio: {audio_files[9]}")
    print(f"Scene 11 audio: {audio_files[10]}")

if __name__ == "__main__":
    main()
