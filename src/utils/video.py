import ffmpeg
import tempfile
import os
import logging

logger = logging.getLogger(__name__)


class VideoProcessor:
    @staticmethod
    def process_to_webm(file_data: bytes, size: int = 512, duration: int = 3) -> bytes:
        """Convert video/gif/media to Telegram-compatible WEBM sticker (VP9, max 3s, max size)"""
        with tempfile.NamedTemporaryFile(suffix=".input", delete=False) as in_file:
            in_file.write(file_data)
            in_path = in_file.name

        out_path = in_path + ".webm"

        try:
            # We use a complex filter to scale and pad to EXACTLY size x size while keeping aspect ratio
            # Then encode with vp9, no audio, and limit duration
            (
                ffmpeg.input(in_path, t=duration)
                .filter(
                    "scale", f"w=min({size}\,{size}*iw/ih):h=min({size}\,{size}*ih/iw)"
                )
                .filter("pad", size, size, "(ow-iw)/2", "(oh-ih)/2", color="0x00000000")
                .output(
                    out_path,
                    vcodec="libvpx-vp9",
                    pix_fmt="yuva420p",
                    crf=30,
                    bitrate="256k",
                    an=None,
                    metadata="-title",
                    loglevel="error",
                )
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True)
            )

            with open(out_path, "rb") as f:
                return f.read()
        except ffmpeg.Error as e:
            logger.error(f"FFmpeg error: {e.stderr.decode()}")
            raise Exception(f"Failed to process video: {e.stderr.decode()}")
        finally:
            if os.path.exists(in_path):
                os.remove(in_path)
            if os.path.exists(out_path):
                os.remove(out_path)

    @staticmethod
    def extract_frame(file_data: bytes) -> bytes:
        """Extract the first frame of a video/gif as a PNG"""
        with tempfile.NamedTemporaryFile(suffix=".input", delete=False) as in_file:
            in_file.write(file_data)
            in_path = in_file.name

        out_path = in_path + ".png"

        try:
            (
                ffmpeg.input(in_path)
                .filter("select", "eq(n,0)")
                .output(out_path, vframes=1, loglevel="error")
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True)
            )

            with open(out_path, "rb") as f:
                return f.read()
        except ffmpeg.Error as e:
            logger.error(f"FFmpeg frame extraction error: {e.stderr.decode()}")
            # Fallback: maybe it's just an image already?
            return file_data
        finally:
            if os.path.exists(in_path):
                os.remove(in_path)
            if os.path.exists(out_path):
                os.remove(out_path)
