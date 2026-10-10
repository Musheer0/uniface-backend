"""ffmpeg remux command: single trailing output (regression test for the old
duplicate-output_path bug in blur_video_with_timestamps)."""

from src.lib.blur_video import build_remux_command
from src.lib.ffmpeg import build_ffmpeg_command


def test_single_trailing_output():
    cmd = build_ffmpeg_command("temp.mp4", "orig.mp4", "out.mp4")
    assert cmd[0] == "ffmpeg"
    assert cmd.count("out.mp4") == 1
    assert cmd[-1] == "out.mp4"


def test_expected_flags():
    cmd = build_ffmpeg_command("t.mp4", "o.mp4", "out.mp4")
    for flag in (["-y", "-map", "0:v:0", "-map", "1:a:0?",
                  "-c:v", "libx264", "-preset", "medium", "-crf", "23",
                  "-c:a", "aac", "-shortest"]):
        assert flag in cmd


def test_video_helper_delegates():
    assert (
        build_remux_command("t.mp4", "o.mp4", "out.mp4")
        == build_ffmpeg_command("t.mp4", "o.mp4", "out.mp4")
    )
