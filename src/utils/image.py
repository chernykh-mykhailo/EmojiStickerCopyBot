import io
import logging
from PIL import Image

logger = logging.getLogger(__name__)

_rembg_session = None


def get_rembg_session():
    """Lazy-load and cache rembg silueta session"""
    global _rembg_session
    if _rembg_session is None:
        try:
            from rembg import new_session

            _rembg_session = new_session("silueta")
        except Exception as e:
            logger.error(f"Failed to load rembg session: {e}")
    return _rembg_session


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
    def remove_background(img: Image.Image) -> Image.Image:
        """Remove background using AI segmentation (rembg silueta model)"""
        if img.mode != "RGBA":
            img = img.convert("RGBA")

        # Downscale large images before AI segmentation to speed up CPU inference
        max_dim = max(img.width, img.height)
        if max_dim > 512:
            img.thumbnail((512, 512), Image.LANCZOS)

        session = get_rembg_session()
        if session:
            try:
                from rembg import remove

                return remove(img, session=session)
            except Exception as e:
                logger.error(f"rembg removal failed: {e}")
        return img

    @staticmethod
    def prepare_regular(file_data: bytes) -> bytes:
        """Resize to EXACTLY 512x512 for regular stickers"""
        img = Image.open(io.BytesIO(file_data))
        return ImageProcessor._fit_and_pad(img, 512)

    @staticmethod
    def prepare_emoji(file_data: bytes) -> bytes:
        """Resize to EXACTLY 100x100 for emoji stickers"""
        img = Image.open(io.BytesIO(file_data))
        return ImageProcessor._fit_and_pad(img, 100)

    @staticmethod
    def prepare_emoji_nobg(file_data: bytes) -> bytes:
        """Resize to 100x100 and clear background using AI segmentation"""
        img = Image.open(io.BytesIO(file_data))
        img = ImageProcessor.remove_background(img)
        return ImageProcessor._fit_and_pad(img, 100)

    @staticmethod
    def get_placeholder(size: int = 512) -> bytes:
        """Generate a simple transparent placeholder of exact size"""
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        out = io.BytesIO()
        img.save(out, format="WEBP", lossless=True)
        return out.getvalue()
