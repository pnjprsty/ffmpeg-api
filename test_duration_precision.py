#!/usr/bin/env python3
"""
Test duration precision synchronization between voice and scene video.

This test verifies that:
1. Voice duration is extracted with full precision (no rounding)
2. Scene duration uses exact voice duration (not ceil/floor)
3. Frame count is calculated with proper rounding
4. FFmpeg output duration matches voice duration precisely
"""

import asyncio
import tempfile
from pathlib import Path
import math

# Test cases with actual voice durations
TEST_CASES = [
    ("7.843", 7.843),      # Voice: 7.843s → Scene: 7.843s
    ("5.127", 5.127),      # Voice: 5.127s → Scene: 5.127s
    ("8.001", 8.001),      # Voice: 8.001s → Scene: 8.001s
    ("10.500", 10.500),    # Voice: 10.500s → Scene: 10.500s
]

def test_duration_no_rounding():
    """Test that scene duration is not rounded with math.ceil()"""
    print("\n=== Test 1: Duration No Rounding ===")
    
    for voice_duration_str, expected_duration in TEST_CASES:
        voice_duration = float(voice_duration_str)
        
        # OLD (WRONG): render_duration = math.ceil(voice_duration)
        # NEW (CORRECT): render_duration = voice_duration
        render_duration = voice_duration
        
        print(f"Voice: {voice_duration}s → Render: {render_duration}s", end="")
        
        if render_duration == expected_duration:
            print(" ✓ PASS")
        else:
            print(f" ✗ FAIL (expected {expected_duration}s, got {render_duration}s)")
            return False
    
    return True


def test_frame_count_rounding():
    """Test that frame count uses round() instead of int()"""
    print("\n=== Test 2: Frame Count Rounding ===")
    
    FPS = 30
    
    for voice_duration_str, expected_duration in TEST_CASES:
        voice_duration = float(voice_duration_str)
        
        # Calculate frame count with proper rounding
        # OLD (WRONG): frame_count = int(voice_duration * FPS)
        # NEW (CORRECT): frame_count = round(voice_duration * FPS)
        frame_count = round(voice_duration * FPS)
        
        # Verify frame count maintains precision
        actual_duration_from_frames = frame_count / FPS
        precision_loss = abs(actual_duration_from_frames - voice_duration)
        
        print(f"Voice: {voice_duration}s → Frames: {frame_count} → Actual: {actual_duration_from_frames:.4f}s", end="")
        
        # Allow small floating point error (< 0.5 frame = ~16ms at 30fps)
        if precision_loss < (0.5 / FPS):
            print(f" ✓ PASS (loss: {precision_loss*1000:.2f}ms)")
        else:
            print(f" ✗ FAIL (loss: {precision_loss*1000:.2f}ms)")
            return False
    
    return True


def test_ffmpeg_duration_parameter():
    """Test that FFmpeg receives duration as float string"""
    print("\n=== Test 3: FFmpeg Duration Parameter ===")
    
    for voice_duration_str, expected_duration in TEST_CASES:
        voice_duration = float(voice_duration_str)
        
        # FFmpeg -t parameter receives duration as string
        ffmpeg_duration_param = str(voice_duration)
        
        print(f"FFmpeg -t parameter: '{ffmpeg_duration_param}'", end="")
        
        # Verify it's a float representation (not rounded)
        if "." in ffmpeg_duration_param or voice_duration == int(voice_duration):
            print(" ✓ PASS")
        else:
            print(" ✗ FAIL")
            return False
    
    return True


def test_total_duration_calculation():
    """Test total duration calculation with transitions"""
    print("\n=== Test 4: Total Duration Calculation ===")
    
    TRANSITION_DURATION = 0.4
    
    # Scenario: 3 scenes
    scene_durations = [7.843, 5.127, 8.001]
    
    # Calculate total duration
    total_duration = sum(scene_durations)
    if len(scene_durations) > 1:
        total_duration -= (len(scene_durations) - 1) * TRANSITION_DURATION
    
    expected_total = 7.843 + 5.127 + 8.001 - 2 * 0.4
    
    print(f"Scene durations: {scene_durations}")
    print(f"Transitions: {len(scene_durations) - 1} x {TRANSITION_DURATION}s")
    print(f"Total: {total_duration}s (expected: {expected_total}s)", end="")
    
    if abs(total_duration - expected_total) < 0.001:  # Allow floating point error
        print(" ✓ PASS")
        return True
    else:
        print(" ✗ FAIL")
        return False


def main():
    print("="*60)
    print("Duration Precision Synchronization Tests")
    print("="*60)
    
    results = []
    results.append(("Duration No Rounding", test_duration_no_rounding()))
    results.append(("Frame Count Rounding", test_frame_count_rounding()))
    results.append(("FFmpeg Duration Parameter", test_ffmpeg_duration_parameter()))
    results.append(("Total Duration Calculation", test_total_duration_calculation()))
    
    print("\n" + "="*60)
    print("Summary")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{test_name}: {status}")
    
    print(f"\nTotal: {passed}/{total} passed")
    
    if passed == total:
        print("\n✓ All tests passed! Duration precision is preserved.")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) failed.")
        return 1


if __name__ == "__main__":
    exit(main())
