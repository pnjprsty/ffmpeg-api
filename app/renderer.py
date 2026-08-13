import logging
import tempfile
import asyncio
from pathlib import Path
from typing import List, Dict, Tuple
import shutil
import subprocess
import re

from .ffmpeg import FFmpegError, get_audio_duration, run_ffmpeg_command
from .models import Scene

logger = logging.getLogger(__name__)

# Video configuration constants
OUTPUT_WIDTH = 1080
OUTPUT_HEIGHT = 1920
FPS = 30
TRANSITION_DURATION = 0.4  # seconds
SUBTITLE_FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"  # Default bold font


class VideoRenderer:
    """Main video rendering engine"""
    
    def __init__(self, output_dir: str = "/output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir = None
    
    def __enter__(self):
        """Create temporary directory for intermediate files"""
        self.temp_dir = tempfile.mkdtemp(prefix="video_render_")
        logger.info(f"Created temporary directory: {self.temp_dir}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Clean up temporary directory"""
        if self.temp_dir and Path(self.temp_dir).exists():
            try:
                shutil.rmtree(self.temp_dir)
                logger.info(f"Cleaned up temporary directory: {self.temp_dir}")
            except Exception as e:
                logger.warning(f"Failed to clean temp directory {self.temp_dir}: {e}")
    
    async def render(self, ide: str, scenes: List[Scene]) -> Tuple[str, float]:
        """
        Render video from scenes
        
        Args:
            ide: Unique identifier for the video
            scenes: List of scenes to render
            
        Returns:
            Tuple of (output_path, total_duration)
        """
        logger.info(f"[Render] Starting render: {ide}")
        logger.info(f"[Render] Processing {len(scenes)} scenes")
        
        # Validate all files exist
        self._validate_scene_files(scenes)
        
        # Get audio durations for each scene
        scene_durations = []
        for i, scene in enumerate(scenes):
            duration = await asyncio.to_thread(get_audio_duration, scene.voice)
            scene_durations.append(duration)
            logger.info(f"[Render] Scene {i+1}/{len(scenes)} - Duration: {duration:.2f}s")
        
        # Create individual scene videos with subtitles
        scene_videos = []
        for i, (scene, duration) in enumerate(zip(scenes, scene_durations)):
            scene_video = await asyncio.to_thread(
                self._create_scene_video,
                scene, 
                duration, 
                i
            )
            scene_videos.append(scene_video)
        
        # Create individual audio files list
        audio_files = [scene.voice for scene in scenes]
        
        # Concatenate videos with transitions
        output_path = self.output_dir / f"{ide}.mp4"
        total_duration = await asyncio.to_thread(
            self._concatenate_with_transitions,
            scene_videos,
            audio_files,
            scene_durations,
            output_path
        )
        
        logger.info(f"[Render] Completed: {output_path}")
        logger.info(f"[Render] Total duration: {total_duration:.2f}s")
        
        return str(output_path), total_duration
    
    def _validate_scene_files(self, scenes: List[Scene]):
        """Validate that all image and voice files exist"""
        for i, scene in enumerate(scenes):
            image_path = Path(scene.image)
            voice_path = Path(scene.voice)
            
            if not image_path.exists():
                raise FFmpegError(f"Scene {i+1} image file not found: {scene.image}")
            
            if not voice_path.exists():
                raise FFmpegError(f"Scene {i+1} voice file not found: {scene.voice}")
            
            logger.debug(f"[Render] Scene {i+1} validated: image={scene.image}, voice={scene.voice}")
    
    def _format_subtitle_text(self, text: str) -> str:
        """
        Format subtitle text with:
        1. Maximum 3 words per line
        2. Maximum 20 characters per line (including spaces)
        3. If 3 words exceed 20 chars, use max 2 words
        4. Each line centered horizontally based on its width
        5. Line breaks before rendering
        
        Example:
        Input: "Teman sering minta pinjam uang tapi lupa bayar"
        Output: "Teman sering minta\npinjam uang tapi\nlupa bayar"
        
        Args:
            text: Raw subtitle text
            
        Returns:
            Formatted text with actual newline characters for FFmpeg drawtext
        """
        # Clean up extra whitespace - preserve word boundaries with punctuation
        words = text.strip().split()
        
        # Group words into lines following rules:
        # - Max 3 words per line
        # - Max 20 characters per line (including spaces)
        # - Don't break words
        lines = []
        current_line = []
        
        for word in words:
            test_line = " ".join(current_line + [word])
            
            # Check both constraints:
            # 1. Less than 3 words (or exactly 3)
            # 2. Total characters <= 20
            if len(current_line) < 3 and len(test_line) <= 20:
                current_line.append(word)
            else:
                # Can't add this word to current line
                if current_line:
                    lines.append(" ".join(current_line))
                current_line = [word]
        
        # Add the last line if it has words
        if current_line:
            lines.append(" ".join(current_line))
        
        # Join with actual newline character (not escaped)
        # FFmpeg drawtext filter needs real newlines for multiline text
        formatted_text = "\n".join(lines)
        return formatted_text
    
    def _escape_text_for_ffmpeg(self, text: str) -> str:
        """
        Escape text for FFmpeg drawtext filter.

        The text value is wrapped with single quotes in the drawtext parameter:
        drawtext=...text='ESCAPED_TEXT':...
        
        FFmpeg filter syntax parsing is multi-layered:
        1. Shell parsing (handled by subprocess.run with list args - no shell interpretation)
        2. FFmpeg filter graph parsing (needs escape of special chars)
        3. drawtext filter parsing (needs escape of special chars)

        Escaping order matters - always escape backslash FIRST.

        Characters that MUST be escaped for FFmpeg filtergraph:
        - Backslash (\): Escape character itself - must be \\
        - Colon (:): Filter parameter separator - must be \:
        - Bracket [ and ]: Filter pad names - must be \[ and \]
        - Percent (%): Variable expansion - must be \%
        - Single quote ('): Delimiter - needs special handling
          In FFmpeg text='...' context, single quotes delimit the text value.
          To include a literal single quote, we use the sequence: '\''
          This ends the current quoted section, adds an escaped quote, and resumes quoting.

        Characters that do NOT need escaping (safe in single-quoted context):
        - Double quote ("): Safe in single quotes
        - Question mark (?): Not a special character
        - Other punctuation: Safe

        Special handling:
        - Newline characters: PRESERVE as-is (actual \n, not escaped)
          FFmpeg drawtext interprets literal newlines for multiline text
        
        Args:
            text: Raw text (may contain newlines, special chars, unicode)
            
        Returns:
            Text safe for use in: drawtext=...text='RESULT':...
        """

        # 1. Escape backslash FIRST (before any other escaping)
        text = text.replace("\\", "\\\\")

        # 2. Escape FFmpeg filter parameter separator (colon)
        text = text.replace(":", "\\:")

        # 3. Escape filtergraph special characters (brackets)
        text = text.replace("[", "\\[")
        text = text.replace("]", "\\]")

        # 4. Escape percent (variable expansion character)
        text = text.replace("%", "\\%")

        # 5. Handle single quotes using FFmpeg's quote-escaping mechanism
        # In FFmpeg, to include a literal single quote in single-quoted context:
        # 'text with ' quote' becomes 'text with '\''quote'
        # This is done by: end quote, add escaped quote, start quote again
        text = text.replace("'", "'\\''")

        # NOTE: Double quotes and question marks do NOT need escaping.
        # NOTE: Actual newline characters are PRESERVED - they are NOT escaped.
        
        return text
    
    def _create_scene_video(self, scene: Scene, duration: float, scene_index: int) -> str:
        """
        Create single scene video with image, ken burns effect, and subtitle
        
        Args:
            scene: Scene object
            duration: Scene duration in seconds
            scene_index: Index of scene (for logging)
            
        Returns:
            Path to scene video file
        """
        logger.info(f"[Render] Creating scene video {scene_index+1}")
        
        scene_path = Path(self.temp_dir) / f"scene_{scene_index:03d}.mp4"
        
        # Format subtitle: max 3 words per line with line breaks
        formatted_subtitle = self._format_subtitle_text(scene.subtitleText)
        escaped_text = self._escape_text_for_ffmpeg(formatted_subtitle)
        
        # Log the subtitle transformation for debugging
        logger.info(f"[Render] Scene {scene_index+1} subtitle processing:")
        logger.info(f"[Render]   Original: {repr(scene.subtitleText)}")
        logger.info(f"[Render]   Formatted: {repr(formatted_subtitle)}")
        logger.info(f"[Render]   Escaped: {repr(escaped_text)}")
        
        # Ken Burns effect parameters
        zoom_start = 1.0
        zoom_end = 1.05  # Subtle 5% zoom in
        pan_x = 0.0  # No horizontal pan
        pan_y = 0.02  # Slight vertical movement
        
        # Filter components: scale proportionally without cropping, then pad to 1080x1920
        # Step 1: Scale image proportionally without exceeding canvas, keeping aspect ratio
        # Step 2: Add padding with black background to reach final dimensions
        # Step 3: Apply Ken Burns zoom effect
        # Step 4: Apply subtitle on top of final canvas, centered with x=(w-text_w)/2
        font_filter = (
            f"scale={OUTPUT_WIDTH}:{OUTPUT_HEIGHT}:force_original_aspect_ratio=decrease,"
            f"pad={OUTPUT_WIDTH}:{OUTPUT_HEIGHT}:(ow-iw)/2:(oh-ih)/2:color=black,"
            f"zoompan=z='zoom+({zoom_end}-{zoom_start})/{duration}':"
            f"x='iw/2-(iw/zoom/2)+{pan_x}*t/{duration}':"
            f"y='ih/2-(ih/zoom/2)+{pan_y}*t/{duration}':"
            f"d={int(duration*FPS)}:s={OUTPUT_WIDTH}x{OUTPUT_HEIGHT},"
            f"fps={FPS},"
            f"drawtext=fontfile={SUBTITLE_FONT}:"
            f"text='{escaped_text}':"
            f"fontcolor=white:"
            f"fontsize=60:"
            f"borderw=3:"
            f"bordercolor=black:"
            f"shadowcolor=black:"
            f"shadowx=2:"
            f"shadowy=2:"
            f"box=1:"
            f"boxcolor=black@0.3:"
            f"boxborderw=10:"
            f"x=(w-text_w)/2:"
            f"y=h-text_h-100"
        )
        
        # FFmpeg command for creating scene video with image, ken burns, and subtitle
        cmd = [
            "ffmpeg",
            "-y",
            "-loop", "1",
            "-i", scene.image,
            "-vf", font_filter,
            "-t", str(duration),
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-preset", "medium",
            "-crf", "23",
            str(scene_path)
        ]
        
        # Log the final filter expression for debugging
        logger.info(f"[Render] Scene {scene_index+1} FFmpeg filter:")
        logger.info(f"[Render]   {repr(font_filter)}")
        logger.debug(f"[Render] Full command: {' '.join(cmd)}")
        
        try:
            run_ffmpeg_command(cmd, timeout=60)
            logger.info(f"[Render] Scene {scene_index+1} video created: {scene_path}")
            return str(scene_path)
        except FFmpegError as e:
            logger.error(f"[Render] Failed to create scene video {scene_index+1}: {e}")
            # Fallback: create simple video without effects
            return self._create_simple_scene_video(scene, duration, scene_index)
    
    def _create_simple_scene_video(self, scene: Scene, duration: float, scene_index: int) -> str:
        """Fallback method to create simple scene video without effects"""
        logger.warning(f"[Render] Using simple video for scene {scene_index+1}")
        
        scene_path = Path(self.temp_dir) / f"scene_simple_{scene_index:03d}.mp4"
        
        # Format subtitle: max 3 words per line with line breaks
        formatted_subtitle = self._format_subtitle_text(scene.subtitleText)
        escaped_text = self._escape_text_for_ffmpeg(formatted_subtitle)
        
        # Simple filter without zoom effect - scale proportionally and pad with black background
        simple_filter = (
            f"scale={OUTPUT_WIDTH}:{OUTPUT_HEIGHT}:force_original_aspect_ratio=decrease,"
            f"pad={OUTPUT_WIDTH}:{OUTPUT_HEIGHT}:(ow-iw)/2:(oh-ih)/2:color=black,"
            f"fps={FPS},"
            f"drawtext=fontfile={SUBTITLE_FONT}:"
            f"text='{escaped_text}':"
            f"fontcolor=white:"
            f"fontsize=60:"
            f"borderw=3:"
            f"bordercolor=black:"
            f"shadowcolor=black:"
            f"shadowx=2:"
            f"shadowy=2:"
            f"box=1:"
            f"boxcolor=black@0.3:"
            f"boxborderw=10:"
            f"x=(w-text_w)/2:"
            f"y=h-text_h-100"
        )
        
        cmd = [
            "ffmpeg",
            "-y",
            "-loop", "1",
            "-i", scene.image,
            "-vf", simple_filter,
            "-t", str(duration),
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-preset", "medium",
            "-crf", "23",
            str(scene_path)
        ]
        
        run_ffmpeg_command(cmd, timeout=60)
        return str(scene_path)
    
    def _concatenate_with_transitions(self, scene_videos: List[str], audio_files: List[str],
                                     scene_durations: List[float], output_path: Path) -> float:
        """
        Concatenate scene videos with transitions and audio
        
        Args:
            scene_videos: List of scene video file paths
            audio_files: List of audio file paths
            scene_durations: List of scene durations
            output_path: Output video path
            
        Returns:
            Total duration of final video
        """
        logger.info("[Render] Concatenating scenes with transitions")
        
        # Transition types (cycle through them)
        transitions = ["fade", "smoothleft", "fadeblack", "smoothright", "circleopen"]
        
        # Build FFmpeg command with concat demuxer for videos
        cmd = ["ffmpeg", "-y"]
        
        # Add video inputs
        for video in scene_videos:
            cmd.extend(["-i", video])
        
        # Add audio inputs
        for audio in audio_files:
            cmd.extend(["-i", audio])
        
        # Build filter complex
        num_videos = len(scene_videos)
        num_audios = len(audio_files)
        
        # Video concatenation with xfade
        if num_videos == 1:
            # Single scene, no transitions
            filter_parts = [f"[0:v]setpts=PTS-STARTPTS[v_out]"]
        else:
            # Multiple scenes with transitions
            filter_parts = []
            
            # First video
            filter_parts.append(f"[0:v]setpts=PTS-STARTPTS[v0]")
            
            # Build transition chain
            current_output = "v0"
            for i in range(1, num_videos):
                transition = transitions[(i - 1) % len(transitions)]
                offset = sum(scene_durations[:i]) - (i * TRANSITION_DURATION)
                
                filter_parts.append(
                    f"[{current_output}][{i}:v]xfade="
                    f"transition={transition}:"
                    f"duration={TRANSITION_DURATION}:"
                    f"offset={offset}[v{i}]"
                )
                current_output = f"v{i}"
            
            filter_parts.append(f"[{current_output}]format=pix_fmts=yuv420p[v_out]")
        
        # Audio concatenation
        if num_audios == 1:
            audio_filter = f"[{num_videos}:a]aformat=sample_rates=44100[a_out]"
        else:
            audio_inputs = "".join([f"[{num_videos + i}:a]" for i in range(num_audios)])
            audio_filter = f"{audio_inputs}concat=n={num_audios}:v=0:a=1[a_out]"
        
        filter_parts.append(audio_filter)
        
        filter_complex = ";".join(filter_parts)
        
        # Complete FFmpeg command
        cmd.extend([
            "-filter_complex", filter_complex,
            "-map", "[v_out]",
            "-map", "[a_out]",
            "-c:v", "libx264",
            "-c:a", "aac",
            "-b:a", "192k",
            "-pix_fmt", "yuv420p",
            "-preset", "medium",
            "-crf", "23",
            "-shortest",
            str(output_path)
        ])
        
        # Log the command for debugging
        logger.debug(f"FFmpeg filter_complex: {filter_complex}")
        
        run_ffmpeg_command(cmd, timeout=300)
        
        # Calculate total duration
        total_duration = sum(scene_durations)
        if len(scene_durations) > 1:
            total_duration -= (len(scene_durations) - 1) * TRANSITION_DURATION
        
        return total_duration
