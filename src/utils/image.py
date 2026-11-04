import io
import logging
from typing import Any
from PIL import Image

logger = logging.getLogger(__name__)

_rembg_sessions: dict[str, Any] = {}

MODEL_MAPPING = {
    "isnet": "isnet-general-use",
    "isnet-general-use": "isnet-general-use",
    "silueta": "silueta",
    "u2net": "u2net",
}


def get_rembg_session(model: str = "isnet-general-use"):
    """Lazy-load and cache rembg session by model name"""
    global _rembg_sessions
    model_name = MODEL_MAPPING.get(model, model)
    if model_name not in _rembg_sessions:
        try:
            from rembg import new_session

            _rembg_sessions[model_name] = new_session(model_name)
        except Exception as e:
            logger.error(f"Failed to load rembg session for {model_name}: {e}")
            if model_name != "silueta":
                return get_rembg_session("silueta")
    return _rembg_sessions.get(model_name)


class ImageProcessor:
    @staticmethod
    def _fit_and_pad(img: Image.Image, size: int) -> bytes:
        """Resize image to fit into size x size with padding to keep aspect ratio"""
        if img.mode != "RGBA":
            img = img.convert("RGBA")

        # Resize to fit inside size x size
        img.thumbnail((size, size), Image.LANCZOS)

        # Create canvas of exact size
        new_img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        # Center
        x = (size - img.width) // 2
        y = (size - img.height) // 2
        new_img.paste(img, (x, y))

        out = io.BytesIO()
        # Telegram likes WebP for stickers/emojis now
        # For emojis, we MUST stay under 64KB.
        if size <= 100:
            quality = 95
            new_img.save(out, format="WEBP", quality=quality, lossy=True)
            while out.tell() > 64000 and quality > 10:
                quality -= 10
                out = io.BytesIO()
                new_img.save(out, format="WEBP", quality=quality, lossy=True)
        else:
            new_img.save(out, format="WEBP", lossless=True)

        return out.getvalue()

    @staticmethod
    def _solidify_alpha(img: Image.Image, threshold: int = 90) -> Image.Image:
        """Make foreground opaque to prevent ghostly/translucent emojis on dark themes"""
        if img.mode != "RGBA":
            return img
        import numpy as np

        arr = np.array(img)
        a = arr[:, :, 3]
        new_a = np.zeros_like(a)
        mask_solid = a >= threshold
        mask_trans = (a > 30) & (a < threshold)
        new_a[mask_solid] = 255
        if np.any(mask_trans):
            new_a[mask_trans] = (
                (a[mask_trans] - 30) / float(threshold - 30) * 255
            ).astype(np.uint8)
        arr[:, :, 3] = new_a
        return Image.fromarray(arr)

    @staticmethod
    def remove_background(img: Image.Image, model: str = "isnet-general-use") -> Image.Image:
        """Remove background using AI segmentation (defaults to isnet-general-use)"""
        if img.mode != "RGBA":
            img = img.convert("RGBA")

        # Downscale large images before AI segmentation to speed up CPU inference
        max_dim = max(img.width, img.height)
        if max_dim > 512:
            img.thumbnail((512, 512), Image.LANCZOS)

        session = get_rembg_session(model)
        if session:
            try:
                from rembg import remove

                res = remove(img, session=session)
                return ImageProcessor._solidify_alpha(res)
            except Exception as e:
                logger.error(f"rembg removal failed: {e}")
        return img

    @staticmethod
    def prepare_regular(file_data: bytes) -> bytes:
        """Resize to EXACTLY 512x512 for regular stickers"""
        img = Image.open(io.BytesIO(file_data))
        return ImageProcessor._fit_and_pad(img, 512)

    @staticmethod
    def prepare_regular_nobg(file_data: bytes, model: str = "isnet-general-use") -> bytes:
        """Resize to 512x512 and clear background"""
        img = Image.open(io.BytesIO(file_data))
        img = ImageProcessor.remove_background(img, model=model)
        return ImageProcessor._fit_and_pad(img, 512)

    @staticmethod
    def prepare_emoji(file_data: bytes) -> bytes:
        """Resize to EXACTLY 100x100 for emoji stickers"""
        img = Image.open(io.BytesIO(file_data))
        return ImageProcessor._fit_and_pad(img, 100)

    @staticmethod
    def prepare_emoji_nobg(file_data: bytes, model: str = "isnet-general-use") -> bytes:
        """Resize to 100x100 and clear background using AI segmentation"""
        img = Image.open(io.BytesIO(file_data))
        img = ImageProcessor.remove_background(img, model=model)
        return ImageProcessor._fit_and_pad(img, 100)

    @staticmethod
    def get_placeholder(size: int = 512) -> bytes:
        """Generate a simple transparent placeholder of exact size"""
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        out = io.BytesIO()
        img.save(out, format="WEBP", lossless=True)
        return out.getvalue()
