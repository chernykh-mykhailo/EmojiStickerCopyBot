# pyrefly: ignore [missing-import]
import ffmpeg
import tempfile
import os
import logging
from PIL import Image

logger = logging.getLogger(__name__)


class VideoProcessor:
    @staticmethod
    def process_to_webm(
        file_data: bytes, size: int = 512, duration: float = 2.9
    ) -> bytes:
        """Convert video/gif/media to Telegram-compatible WEBM sticker (VP9, max 3s, max size)"""
        with tempfile.NamedTemporaryFile(suffix=".input", delete=False) as in_file:
            in_file.write(file_data)
            in_path = in_file.name

        out_path = in_path + ".webm"

        # Determine bitrate based on size (emojis are 100x100 and have 64KB limit)
        # 64KB = 512Kb. Over 3 seconds = ~170Kbps. Use 128k to be safe.
        bitrate = "128k" if size <= 128 else "256k"
        crf = 35 if size <= 128 else 30

        try:
            # We use a complex filter to scale and pad to EXACTLY size x size while keeping aspect ratio
            # Then encode with vp9, no audio, and limit duration
            (
                ffmpeg.input(in_path)
                .filter(
                    "scale",
                    w=f"if(gt(iw,ih),{size},-2)",
                    h=f"if(gt(iw,ih),-2,{size})",
                )
                .filter(
                    "pad",
                    w=size,
                    h=size,
                    x=f"({size}-iw)/2",
                    y=f"({size}-ih)/2",
                    color="black@0",
                )
                .output(
                    out_path,
                    t=duration,
                    vcodec="libvpx-vp9",
                    pix_fmt="yuva420p",
                    crf=crf,
                    bitrate=bitrate,
                    r=30,
                    g=60,
                    an=None,
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
    def process_video_nobg(
        file_data: bytes, size: int = 100, duration: float = 2.8, model: str = "isnet-general-use"
    ) -> bytes:
        """Extract frames, remove background on each frame using rembg, and re-encode to transparent WEBM sticker"""
        from utils.image import ImageProcessor

        with tempfile.TemporaryDirectory() as tmpdir:
            in_video = os.path.join(tmpdir, "input.webm")
            with open(in_video, "wb") as f:
                f.write(file_data)

            frames_pattern = os.path.join(tmpdir, "frame_%04d.png")
            fps = 12 if size <= 100 else 15
            try:
                (
                    ffmpeg.input(in_video, t=duration)
                    .filter("fps", fps=fps)
                    .filter(
                        "scale",
                        w=f"if(gt(iw,ih),{size},-2)",
                        h=f"if(gt(iw,ih),-2,{size})",
                    )
                    .filter(
                        "pad",
                        w=size,
                        h=size,
                        x=f"({size}-iw)/2",
                        y=f"({size}-ih)/2",
                        color="black@0",
                    )
                    .output(frames_pattern, loglevel="error")
                    .overwrite_output()
                    .run(capture_stdout=True, capture_stderr=True)
                )
            except ffmpeg.Error as e:
                logger.error(f"FFmpeg frame extraction error: {e.stderr.decode() if e.stderr else e}")
                return VideoProcessor.process_to_webm(file_data, size=size, duration=duration)

            frame_files = sorted([f for f in os.listdir(tmpdir) if f.startswith("frame_") and f.endswith(".png")])
            if not frame_files:
                return VideoProcessor.process_to_webm(file_data, size=size, duration=duration)

            for f_name in frame_files:
                p = os.path.join(tmpdir, f_name)
                try:
                    img = Image.open(p)
                    nobg_img = ImageProcessor.remove_background(img, model=model)
                    nobg_img.save(p)
                except Exception as ex:
                    logger.warning(f"Error cutting frame {f_name}: {ex}")

            out_webm = os.path.join(tmpdir, "out.webm")
            crf = 38 if size <= 100 else 30
            bitrate = "96k" if size <= 100 else "256k"

            try:
                (
                    ffmpeg.input(frames_pattern, framerate=fps)
                    .output(
                        out_webm,
                        vcodec="libvpx-vp9",
                        pix_fmt="yuva420p",
                        crf=crf,
                        bitrate=bitrate,
                        an=None,
                        loglevel="error",
                    )
                    .overwrite_output()
                    .run(capture_stdout=True, capture_stderr=True)
                )

                # For emoji (size <= 100), Telegram strictly requires <= 64KB (65536 bytes)
                if size <= 100 and os.path.getsize(out_webm) > 64000:
                    (
                        ffmpeg.input(frames_pattern, framerate=10)
                        .output(
                            out_webm,
                            vcodec="libvpx-vp9",
                            pix_fmt="yuva420p",
                            crf=46,
                            bitrate="64k",
                            an=None,
                            loglevel="error",
                        )
                        .overwrite_output()
                        .run(capture_stdout=True, capture_stderr=True)
                    )

                with open(out_webm, "rb") as f:
                    return f.read()
            except ffmpeg.Error as e:
                logger.error(f"FFmpeg webm encoding error: {e.stderr.decode() if e.stderr else e}")
                return VideoProcessor.process_to_webm(file_data, size=size, duration=duration)

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
