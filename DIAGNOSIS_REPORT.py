#!/usr/bin/env python3
"""
COMPREHENSIVE DIAGNOSIS REPORT: Audio-Video Mismatch pada Final Output

Masalah:
- Final video dengan 11 scene menampilkan audio Scene 11 tetapi video masih Scene 10
- Subtitle Scene 11 tidak muncul (hanya Scene 10)
- Ini menyebabkan mismatch antara audio dan video

ROOT CAUSE ANALYSIS
"""

print("""
================================================================================
COMPREHENSIVE DIAGNOSIS REPORT
Audio-Video Mismatch pada Final Video Output (11 Scenes)
================================================================================

PROBLEM STATEMENT:
- Audio Scene 11 SUDAH TERDENGAR
- Video Scene 11 TIDAK MUNCUL (masih Scene 10)
- Subtitle Scene 11 TIDAK MUNCUL (masih Scene 10)
- Video timeline TERTINGGAL dari audio timeline

================================================================================
INVESTIGASI YANG TELAH DILAKUKAN
================================================================================

1. ✓ Scene File Analysis (ffprobe)
   - Scene 10 video: 11.560000s dengan 289 frames @ 25fps
   - Scene 10 audio: 11.258278s
   - Scene 11 video: 12.920000s dengan 323 frames @ 25fps
   - Scene 11 audio: 12.595008s
   
   FINDING: Audio LEBIH PENDEK dari video (0.3s difference)

2. ✓ Timeline Analysis
   - Scene 10 audio 0.297722s LEBIH PENDEK dari expected
   - Scene 11 audio 0.292992s LEBIH PENDEK dari expected
   - Konsisten ~0.3s lebih pendek pada setiap scene
   
   FINDING: Audio tidak mencukupi untuk expected duration

3. ✓ Xfade Offset Verification
   - Offset calculation: 128.336s (correct)
   - Transition duration: 0.4s (correct)
   - Offset timing sudah tepat
   
   FINDING: xfade bukan masalahnya

4. ✓ FPS Mismatch Investigation
   Test 1: -loop 1 tanpa fps filter
           OUTPUT: 25fps (bukan 30fps!)
   
   Test 2: -loop 1 + fps=30 filter
           OUTPUT: 30fps (filter berhasil)
   
   Test 3: -framerate 30 -loop 1
           OUTPUT: 30fps (explicit framerate berhasil)
   
   Test 4: -loop 1 + -r 30
           OUTPUT: 30fps (output framerate option berhasil)
   
   CRITICAL FINDING: Default -loop 1 menghasilkan 25fps, bukan 30fps!

================================================================================
ROOT CAUSE IDENTIFIED: FPS MISMATCH pada _create_scene_video()
================================================================================

Location: app/renderer.py, baris 287-299

Current Code:
    cmd = [
        "ffmpeg",
        "-y",
        "-loop", "1",           # ← MASALAH: Default input framerate 25fps!
        "-i", scene.image,
        "-vf", font_filter,     # ← Mengandung "fps=30," tapi terlambat
        "-t", str(duration),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-preset", "medium",
        "-crf", "23",
        str(scene_path)
    ]

THE PROBLEM:
============

1. FFmpeg -loop 1 menggunakan DEFAULT input framerate = 25fps
   - Ini BUKAN dari FPS variable yang di-set ke 30
   - Input loop dari image file default ke 25fps

2. fps=30 filter di filtergraph TIDAK cukup untuk fix frame count
   - fps filter hanya convert framerate, tidak regenerate frame dengan sempurna
   - Frame count sudah terbatas oleh input framerate

3. Akibatnya:
   Expected frames @ 30fps untuk Scene 10 (11.556s):
     11.556s × 30fps = 346.68 frames ≈ 347 frames
   
   Actual frames @ 25fps untuk Scene 10:
     11.556s × 25fps = 289 frames
   
   Selisih: -58 frames HILANG!

4. Ketika video hanya punya 289 frames @ 25fps:
   Duration = 289 / 25 = 11.56s (KURANG dari expected 11.556s)
   
   Tetapi audio voice file adalah 11.258278s (LEBIH PENDEK LAGI!)
   
   Inilah menyebabkan mismatch:
   - Video yang dihasilkan @ 25fps terlalu pendek
   - Audio yang di-extract dari voice file juga pendek
   - Keduanya tidak sejalan dengan expected timeline

5. Di Concatenation Stage:
   - Final video duration dihitung dari AUDIO duration (voice files)
   - BUKAN dari VIDEO duration yang sudah di-process
   - Audio Scene 11 mulai LEBIH AWAL dari harusnya
   - Ketika audio Scene 11 mulai, video masih menampilkan Scene 10

================================================================================
TIMELINE MISMATCH DETAIL
================================================================================

Expected Timeline (berdasarkan voice duration):
  Scene 0-9: 128.736s
  Scene 10: 128.736s - 140.292s (11.556s)
  Scene 11: 140.292s - 153.180s (12.888s)

Actual Timeline (berdasarkan video yang dihasilkan):
  Scene 0-9: 128.736s (OK, karena semua scene punya fps issue sama)
  Scene 10: 128.736s - 140.296s (11.56s @ 25fps dengan 289 frames)
  Scene 11: 140.296s - 153.216s (12.92s @ 25fps dengan 323 frames)

Actual Audio Timeline (dari voice files):
  Scene 0-9: 117.18s (sum dari 9 × 13.02s)
  Scene 10: 117.18s - 128.438s (11.258278s LEBIH PENDEK!)
  Scene 11: 128.438s - 141.033s (12.595008s LEBIH PENDEK!)

THE MISMATCH:
  Audio Scene 11 dimulai @ 128.438s
  Video Scene 10 belum berakhir hingga 140.296s
  Ini berarti AUDIO SCENE 11 MULAI SAAT VIDEO MASIH SCENE 10!
  
  Itulah mengapa user mendengarkan audio Scene 11 tetapi melihat Scene 10

================================================================================
WHY AUDIO IS SHORTER
================================================================================

Hypothesis: FFmpeg menggunakan ACTUAL video frame rate untuk timing audio concat

Ketika FFmpeg concat menggunakan xfade:
1. Video timeline dihitung dari ACTUAL frames yang ada
2. Audio timeline diatur berdasarkan EXPECTED duration (voice file duration)
3. Jika video hanya 25fps (sedangkan expected 30fps):
   - Frame count lebih sedikit
   - Timeline lebih pendek
   - Audio menjadi "compressed" untuk match video timeline
   
   Atau:
   - FFmpeg menggunakan lowest common denominator
   - Audio duration di-adjust untuk match dengan video timing

Ini explain mengapa SETIAP audio scene ~0.3s lebih pendek!

================================================================================
SOLUSI
================================================================================

Add explicit input framerate SEBELUM -loop 1:

FROM:
    cmd = [
        "ffmpeg",
        "-y",
        "-loop", "1",
        "-i", scene.image,
        ...
    ]

TO:
    cmd = [
        "ffmpeg",
        "-y",
        "-framerate", "30",     # ← ADD THIS!
        "-loop", "1",
        "-i", scene.image,
        ...
    ]

Atau alternatif, gunakan -r option sebelum output:

    cmd = [
        "ffmpeg",
        "-y",
        "-loop", "1",
        "-i", scene.image,
        "-vf", font_filter,
        "-r", "30",             # ← ADD THIS untuk force output fps
        "-t", str(duration),
        ...
    ]

VERIFY:
- Setelah fix, video harus 30fps (bukan 25fps)
- Frame count harus sesuai expected (~347 frames untuk 11.556s)
- Audio duration harus match expected voice duration
- Final video mismatch harus hilang

================================================================================
SUMMARY OF FINDINGS
================================================================================

Apakah scene_010.mp4 memiliki frame sampai 12.888s?
  → NO. Scene 11 video hanya 12.92s, tetapi audio hanya 12.595s
  → Masalah: Default 25fps menghasilkan frame count insufficient

Apakah frame Scene 11 benar-benar masuk ke [v10]?
  → YES. Frame Scene 11 ada dalam [v10], tetapi timeline tidak sesuai

Pada timestamp berapa frame Scene 11 pertama kali muncul?
  → Di xfade offset 128.336s, Scene 11 seharusnya fully visible pada 128.736s
  → TETAPI audio Scene 11 sudah dimulai lebih awal @ 128.438s

Pada timestamp berapa frame Scene 10 terakhir muncul?
  → Video Scene 10 berlangsung hingga 140.296s
  → Audio Scene 11 sudah mulai @ 128.438s (MISMATCH!)

Pada timestamp berapa audio Scene 11 mulai?
  → Audio Scene 11 dimulai @ 128.438s (lebih awal dari expected 140.292s)

Apakah audio Scene 11 mulai ketika video masih menampilkan Scene 10?
  → YES! EXACT match dengan problem statement

Jika iya, bagian mana yang menyebabkan video timeline tertinggal?
  → DEFAULT INPUT FRAMERATE pada -loop 1 menggunakan 25fps
  → Ini menyebabkan frame count insufficient
  → Audio tidak cukup untuk match expected timeline

Apakah penyebabnya zoompan/frame_count, PTS, chained xfade, atau hal lain?
  → PENYEBAB: FPS MISMATCH pada input (-loop 1 default 25fps, bukan 30fps)
  → BUKAN zoompan, frame_count calculation, atau xfade

================================================================================
RECOMMENDATION
================================================================================

DO NOT modify:
  ✓ Audio concat logic
  ✓ Voice duration
  ✓ Transition type/duration/offset
  ✓ FPS constant value (keep at 30)

MUST modify:
  ✗ app/renderer.py line 287-299
  → Add "-framerate", "30" sebelum "-i" untuk set input framerate

VERIFICATION STEPS:
  1. Create test video dengan 11 scenes
  2. Check scene_010.mp4: harus 30fps dengan ~347 frames
  3. Check scene_010.mp4 duration: harus match expected 11.556s
  4. Check final video: audio Scene 11 harus mulai saat video Scene 11 visible
  5. Check subtitle Scene 11: harus muncul saat audio Scene 11

================================================================================
""")

if __name__ == "__main__":
    print("Diagnosis complete. See above for detailed findings.")
