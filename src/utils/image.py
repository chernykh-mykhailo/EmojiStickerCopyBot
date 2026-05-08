import io
from PIL import Image


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
        """Resize to 100x100 and attempt to clear background"""
        img = Image.open(io.BytesIO(file_data))
        if img.mode != "RGBA":
            img = img.convert("RGBA")

        datas = img.getdata()
        new_data = []
        for item in datas:
            if item[0] > 245 and item[1] > 245 and item[2] > 245:
                new_data.append((255, 255, 255, 0))
            else:
                new_data.append(item)
        img.putdata(new_data)

        return ImageProcessor._fit_and_pad(img, 100)

    @staticmethod
    def get_placeholder(size: int = 512) -> bytes:
        """Generate a simple transparent placeholder of exact size"""
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        out = io.BytesIO()
        img.save(out, format="WEBP", lossless=True)
        return out.getvalue()
