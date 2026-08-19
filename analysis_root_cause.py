#!/usr/bin/env python3
"""
Analisis mendalam tentang xfade timeline dan frame timestamps.

Fokus:
1. Apakah scene_010.mp4 memiliki frame sampai 12.888s?
2. Apakah frame Scene 11 benar-benar masuk ke [v10]?
3. Timeline mismatch antara audio dan video
"""

import json
import subprocess
import tempfile
import os
from pathlib import Path

def run_cmd(cmd):
    """Run command and return output"""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.returncode, result.stdout, result.stderr

def analyze_frame_delivery():
    """
    Analisis apakah video Scene 11 benar-benar memberikan frames sampai durasi penuh.
    
    Key issue:
    - Scene 10 video actual: 11.560000s (expected: 11.556s)
    - Scene 11 video actual: 12.920000s (expected: 12.888s)
    
    Video lebih panjang dari expected, tetapi:
    - Scene 10 audio: 11.258278s (LEBIH PENDEK 0.297722s)
    - Scene 11 audio: 12.595008s (LEBIH PENDEK 0.292992s)
    
    Kemungkinan masalah: Audio lebih pendek dari video!
    """
    
    print("\n" + "="*80)
    print("ANALISIS: MISMATCH AUDIO-VIDEO DURASI")
    print("="*80)
    
    print("\nFINDING #1: Audio LEBIH PENDEK dari Video")
    print("-" * 80)
    print("Scene 10:")
    print(f"  Video duration: 11.560000s")
    print(f"  Audio duration: 11.258278s")
    print(f"  Selisih: -0.301722s (AUDIO LEBIH PENDEK)")
    print("")
    print("Scene 11:")
    print(f"  Video duration: 12.920000s")
    print(f"  Audio duration: 12.595008s")
    print(f"  Selisih: -0.324992s (AUDIO LEBIH PENDEK)")
    print("")
    print("Implikasi:")
    print("  Ketika FFmpeg concat menggabungkan video+audio dengan xfade,")
    print("  jika audio lebih pendek dari video, maka:")
    print("    1. Audio akan mencapai EOF lebih awal")
    print("    2. Jika final output diatur dengan '-t {target_duration}',")
    print("       video terus berjalan tetapi audio sudah selesai")
    print("    3. Ini BISA menyebabkan audio Scene 11 muncul saat video masih Scene 10")
    
    print("\n" + "="*80)
    print("ANALISIS: FRAME COUNT vs EXPECTED FRAMES")
    print("="*80)
    
    print("\nScene 10 (index 9):")
    print(f"  Expected duration: 11.556s")
    print(f"  Expected frames @ 30fps: {11.556 * 30:.2f}")
    print(f"  Expected frames @ 25fps: {11.556 * 25:.2f}")
    print(f"  Actual frames from ffprobe: 289")
    print(f"  Actual FPS detected: 25fps")
    print(f"  Actual duration calculated: 289 / 25 = {289/25:.4f}s")
    print("")
    print("Scene 11 (index 10):")
    print(f"  Expected duration: 12.888s")
    print(f"  Expected frames @ 30fps: {12.888 * 30:.2f}")
    print(f"  Expected frames @ 25fps: {12.888 * 25:.2f}")
    print(f"  Actual frames from ffprobe: 323")
    print(f"  Actual FPS detected: 25fps")
    print(f"  Actual duration calculated: 323 / 25 = {323/25:.4f}s")
    
    print("\n" + "="*80)
    print("CRITICAL FINDING: FPS MISMATCH!")
    print("="*80)
    print("\nProblem:")
    print("  Code menggunakan FPS = 30 untuk generate video frames")
    print("  Tetapi ffmpeg color filter menghasilkan video dengan FPS = 25")
    print("  Ini menyebabkan frame count tidak sesuai expected!")
    print("")
    print("Expected frames untuk Scene 10:")
    print(f"  @ 30fps: {11.556 * 30:.2f} frames = ~347 frames")
    print(f"  Actual @ 25fps: 289 frames")
    print(f"  Selisih: -58 frames HILANG!")
    print("")
    print("Expected frames untuk Scene 11:")
    print(f"  @ 30fps: {12.888 * 30:.2f} frames = ~387 frames")
    print(f"  Actual @ 25fps: 323 frames")
    print(f"  Selisih: -64 frames HILANG!")

def analyze_xfade_offset_problem():
    """
    Analisis masalah offset dalam xfade untuk Scene 10 dan 11.
    
    Data log dari user:
    [v9][10:v]xfade=transition=circleopen:duration=0.4:offset=128.336[v10]
    
    Scene 10 (index 9): 11.556s
    Scene 11 (index 10): 12.888s
    Sum of scenes 0-9: 128.736s (expected)
    """
    
    print("\n\n" + "="*80)
    print("ANALISIS: XFADE OFFSET UNTUK SCENE 10 → 11")
    print("="*80)
    
    print("\nFromatan log user:")
    print("  [v9][10:v]xfade=transition=circleopen:duration=0.4:offset=128.336[v10]")
    print("")
    
    print("Breakdown:")
    print("  [v9] = output dari xfade sebelumnya (Scene 9 transisi ke Scene 10)")
    print("  [10:v] = Scene 11 video input (index 10)")
    print("  offset = 128.336s")
    print("  duration = 0.4s")
    print("")
    
    print("Expected calculation:")
    scenes_0_9_sum = 128.736
    expected_offset = scenes_0_9_sum - 0.4
    print(f"  Sum of scenes 0-9: {scenes_0_9_sum}s")
    print(f"  Expected offset = sum - transition_duration")
    print(f"                  = {scenes_0_9_sum} - 0.4")
    print(f"                  = {expected_offset}s")
    print("")
    
    print("Actual offset from log: 128.336s")
    print(f"Selisih: 128.336 - {expected_offset} = {128.336 - expected_offset}s")
    print("")
    
    print("Implikasi offset:")
    print("  Offset 128.336s berarti xfade transition DIMULAI pada detik 128.336")
    print("  Transition berlangsung 0.4s (128.336 - 128.736)")
    print("  Frame Scene 10 seharusnya visible hingga 128.736s (offset + duration)")
    print("  Frame Scene 11 seharusnya fully visible setelah 128.736s")
    print("")
    print("TAPI!")
    print("  Jika Scene 10 video hanya punya 289 frames @ 25fps = 11.56s")
    print("  Dan Scene 0-9 totalnya berjalan 128.736s")
    print("  MAKA Scene 10 AKAN KEHABISAN FRAME sebelum 128.736s tercapai!")
    print("")
    print("Timeline mismatch:")
    print("  Expected Scene 10 end: 128.736s")
    print("  Actual Scene 10 end: 128.736s (timeline) tapi VIDEO FRAME habis!")
    print("  Ini menyebabkan LOOP FRAME atau FREEZE pada frame terakhir Scene 10")

def analyze_audio_video_sync():
    """
    Analisis sinkronisasi audio-video berdasarkan actual durations.
    """
    
    print("\n\n" + "="*80)
    print("ANALISIS: AUDIO-VIDEO SYNCHRONIZATION")
    print("="*80)
    
    print("\nTotal scenes: 11")
    print("Target total duration: 141.624s (dari audio)")
    print("")
    
    # Scene durations
    durations = [13.02] * 9 + [11.556, 12.888]
    
    print("Timeline Scene 0-9:")
    cumsum = 0
    for i in range(10):
        cumsum += durations[i]
        print(f"  Scene {i}: {cumsum:.3f}s")
    
    print(f"\nScene 10 (index 9):")
    print(f"  Expected start: {cumsum:.3f}s")
    print(f"  Expected end: {cumsum + durations[9]:.3f}s")
    print(f"  Actual video duration: 11.560000s")
    print(f"  Actual audio duration: 11.258278s")
    print(f"  Actual end @ video: {cumsum + 11.560000:.3f}s")
    print(f"  Actual end @ audio: {cumsum + 11.258278:.3f}s")
    
    cumsum += durations[9]
    
    print(f"\nScene 11 (index 10):")
    print(f"  Expected start: {cumsum:.3f}s")
    print(f"  Expected end: {cumsum + durations[10]:.3f}s")
    print(f"  Actual video duration: 12.920000s")
    print(f"  Actual audio duration: 12.595008s")
    print(f"  Actual end @ video: {cumsum + 12.920000:.3f}s")
    print(f"  Actual end @ audio: {cumsum + 12.595008:.3f}s")
    
    print("")
    print("MISMATCH ANALYSIS:")
    print("")
    print("Ketika final concat dijalankan dengan target_duration=141.624s:")
    print("  1. Audio Scene 10 ends @ 139.994278s (cumsum + 11.258278)")
    print("  2. Audio Scene 11 starts @ 139.994278s")
    print("  3. Audio Scene 11 ends @ 152.589286s (cumsum + 12.595008)")
    print("  4. BUT final output cut at 141.624s (-t flag)")
    print("")
    print("  Video Timeline:")
    print("  1. Video Scene 10 ends @ 140.296000s (cumsum + 11.560000)")
    print("  2. Video Scene 11 starts @ xfade offset")
    print("  3. Video Scene 11 should be fully visible after 140.296s")
    print("")
    print("KESIMPULAN:")
    print("  - Audio Scene 10 lebih pendek 0.297722s")
    print("  - Audio Scene 11 mulai lebih awal dari expected")
    print("  - Ketika audio Scene 11 mulai, video Scene 10 MASIH TERLIHAT")
    print("  - Ini menyebabkan mismatch yang dilaporkan!")

def main():
    analyze_frame_delivery()
    analyze_xfade_offset_problem()
    analyze_audio_video_sync()
    
    print("\n\n" + "="*80)
    print("ROOT CAUSE SUMMARY")
    print("="*80)
    print("""
1. AUDIO ADALAH MASALAHNYA
   - Audio Scene 10: 11.258278s (0.297722s LEBIH PENDEK dari expected 11.556s)
   - Audio Scene 11: 12.595008s (0.292992s LEBIH PENDEK dari expected 12.888s)
   - Audio secara konsisten 0.3s lebih pendek dari expected

2. PENYEBAB: FPS MISMATCH
   - Code menggunakan FPS = 30 saat create scene video
   - Tetapi video yang dihasilkan hanya 25fps (bukan 30fps)
   - Ini menyebabkan frame count tidak cukup
   - Karena frame tidak cukup, audio compressed/shorter

3. AKIBAT: AUDIO MULAI LEBIH AWAL
   - Audio Scene 11 mulai ~0.3s LEBIH AWAL dari expected
   - Saat audio Scene 11 mulai, video masih menampilkan Scene 10
   - Ini EXACT match dengan masalah yang dilaporkan!

4. TIDAK MASALAH XFADE
   - Xfade offset dan transition sudah benar
   - Masalahnya bukan pada video concatenation
   - Masalahnya pada INDIVIDUAL scene video creation

5. TIDAK MASALAH SUBTITLE
   - Subtitle dibakar ke scene video
   - Jika frame Scene 10 masih visible, subtitle Scene 10 juga masih visible
   - Ini bukti bahwa frame Scene 10 yang masih ditampilkan

SOLUSI YANG PERLU DICEK:
- Periksa _create_scene_video() pada line 232-313 di app/renderer.py
- Periksa FPS configuration (line 19: FPS = 30)
- Periksa output dari ffmpeg -t {duration} command
- Verifikasi bahwa video yang dihasilkan benar-benar 30fps atau cek jika video filter mengubah fps
    """)

if __name__ == "__main__":
    main()
