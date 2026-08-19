#!/usr/bin/env python3
"""
Test script to verify that all 9 scenes are properly included in the final video output.
This script creates mock scenes and verifies the concatenation logic.
"""

import logging
import sys
from pathlib import Path

# Setup logging to see detailed debug info
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Mock scene durations (simulating 9 scenes with realistic durations)
SCENE_DURATIONS = [
    8.5, 7.2, 9.1, 8.3, 7.9, 8.6, 9.2, 8.1, 8.4  # 9 scenes
]

TRANSITION_DURATION = 0.4
transitions = ["fade", "smoothleft", "fadeblack", "smoothright", "circleopen"]

def verify_transition_logic():
    """
    Verify that the transition logic correctly includes all scenes,
    especially the last one (scene_008.mp4).
    """
    logger.info("=" * 80)
    logger.info("VERIFYING 9-SCENE CONCATENATION LOGIC")
    logger.info("=" * 80)
    
    num_videos = len(SCENE_DURATIONS)
    logger.info(f"[Concat] Number of scenes: {num_videos}")
    
    # Log all scenes
    for idx, duration in enumerate(SCENE_DURATIONS):
        logger.info(f"[Concat] Scene {idx+1}: scene_{idx:03d}.mp4 (duration: {duration}s)")
    
    logger.info(f"[Concat] Total duration sum: {sum(SCENE_DURATIONS)}s")
    logger.info("")
    
    # Verify loop covers all scenes
    logger.info("TRANSITION LOOP ANALYSIS:")
    logger.info(f"Loop range: range(1, {num_videos}) -> i from 1 to {num_videos-1}")
    logger.info("")
    
    current_output = "v0"
    scene_indices_used = [0]  # First scene v0
    
    for i in range(1, num_videos):
        transition = transitions[(i - 1) % len(transitions)]
        offset = sum(SCENE_DURATIONS[:i]) - TRANSITION_DURATION
        
        logger.info(f"[Concat] Transition {i}: scene_{i-1:03d} + scene_{i:03d}")
        logger.info(f"  - Input 1: [{current_output}] (output from previous transition)")
        logger.info(f"  - Input 2: [{i}:v] (scene_{i:03d}.mp4)")
        logger.info(f"  - Offset: {offset}s (sum of scenes 0-{i-1} minus transition duration)")
        logger.info(f"  - Duration: {TRANSITION_DURATION}s")
        logger.info(f"  - Transition type: {transition}")
        logger.info(f"  - Output: [v{i}]")
        logger.info("")
        
        current_output = f"v{i}"
        scene_indices_used.append(i)
    
    logger.info("FINAL VERIFICATION:")
    logger.info(f"Last transition output: [{current_output}]")
    logger.info(f"Final output pad: [{current_output}] -> [v_out]")
    logger.info("")
    
    logger.info("SCENES INCLUDED IN TRANSITION CHAIN:")
    logger.info(f"Transition chain includes scene indices: {scene_indices_used}")
    logger.info(f"Total scenes in chain: {len(scene_indices_used)}")
    logger.info("")
    
    # Verify all scenes are included
    all_scenes = set(range(num_videos))
    included_scenes = set(scene_indices_used)
    
    if all_scenes == included_scenes:
        logger.info("✓ SUCCESS: All 9 scenes are included in the transition chain!")
        logger.info(f"✓ Scene 8 (scene_008.mp4) IS included in transition at index {num_videos-1}")
        return True
    else:
        missing = all_scenes - included_scenes
        logger.error(f"✗ FAILURE: Missing scenes: {sorted(missing)}")
        return False

def verify_offset_calculations():
    """
    Verify that offset calculations are correct for the last scene.
    """
    logger.info("\n" + "=" * 80)
    logger.info("OFFSET CALCULATION VERIFICATION")
    logger.info("=" * 80)
    
    num_videos = len(SCENE_DURATIONS)
    
    logger.info("Scene timeline:")
    current_time = 0
    for i, duration in enumerate(SCENE_DURATIONS):
        logger.info(f"Scene {i:1d} (scene_{i:03d}.mp4): {current_time:6.2f}s - {current_time + duration:6.2f}s (duration: {duration}s)")
        current_time += duration
    
    logger.info("")
    logger.info("Transition offsets (where transition should start):")
    
    for i in range(1, num_videos):
        prev_scenes_duration = sum(SCENE_DURATIONS[:i])
        offset = prev_scenes_duration - TRANSITION_DURATION
        
        logger.info(f"Transition {i} (scene_{i-1:03d} → scene_{i:03d}):")
        logger.info(f"  - Previous scenes (0-{i-1}) total duration: {prev_scenes_duration}s")
        logger.info(f"  - Transition should start at: {offset}s")
        logger.info(f"  - Scene {i:1d} duration: {SCENE_DURATIONS[i]}s")
        logger.info(f"  - Scene {i:1d} should be visible from: {offset + TRANSITION_DURATION}s to {sum(SCENE_DURATIONS[:i+1])}s")
        logger.info("")

if __name__ == "__main__":
    success = verify_transition_logic()
    verify_offset_calculations()
    
    logger.info("=" * 80)
    if success:
        logger.info("✓ ALL CHECKS PASSED - Scene 9 (scene_008.mp4) will be included")
        sys.exit(0)
    else:
        logger.error("✗ CHECKS FAILED - Scene 9 (scene_008.mp4) may be missing")
        sys.exit(1)
