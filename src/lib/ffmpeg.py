"""Single place that builds the ffmpeg remux command.

Video processing writes anonymized frames to a temporary ``mp4v`` file and
then remuxes: video from the temp file, audio copied from the original.
Output is always H.264 video + AAC audio MP4. ``-map 1:a:0?`` keeps silent
inputs working (audio stream optional), ``-shortest`` stops at the shorter
of the two inputs.
"""

__all__ = ["build_ffmpeg_command"]


def build_ffmpeg_command(temp_video: str, video_path: str, output_path: str) -> list[str]:
    return [
        "ffmpeg",
        "-y",
        # Processed (blurred) video
        "-i", temp_video,
        # Original video (audio source)
        "-i", video_path,
        # Video from processed file
        "-map", "0:v:0",
        # Audio from original file (optional — silent inputs still work)
        "-map", "1:a:0?",
        # Encode video
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "23",
        # Encode audio
        "-c:a", "aac",
        "-shortest",
        output_path,
    ]
