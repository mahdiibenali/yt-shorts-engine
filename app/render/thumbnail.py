import os
import logging
from typing import Optional

from PIL import Image, ImageDraw, ImageFont

from app.config import settings

logger = logging.getLogger(__name__)


class ThumbnailGenerator:
    def __init__(self):
        self.fonts_dir = os.path.join(settings.data_dir, "..", "app", "assets", "fonts")

    def generate(self, title: str, output_path: str, background_path: Optional[str] = None) -> str:
        img = Image.new("RGB", (1280, 720), (20, 20, 30))

        draw = ImageDraw.Draw(img)

        font_path = os.path.join(self.fonts_dir, "Roboto-Bold.ttf")
        try:
            font_large = ImageFont.truetype(font_path, 72)
            font_small = ImageFont.truetype(font_path, 36)
        except (OSError, IOError):
            font_large = ImageFont.load_default()
            font_small = ImageFont.load_default()

        lines = []
        words = title.split()
        line = ""
        for word in words:
            test = line + " " + word if line else word
            bbox = draw.textbbox((0, 0), test, font=font_large)
            if bbox[2] - bbox[0] > 1100:
                lines.append(line)
                line = word
            else:
                line = test
        lines.append(line)

        y_start = 200
        for i, line_text in enumerate(lines):
            bbox = draw.textbbox((0, 0), line_text, font=font_large)
            tw = bbox[2] - bbox[0]
            x = (1280 - tw) // 2
            y = y_start + i * 90
            draw.text((x + 3, y + 3), line_text, font=font_large, fill=(0, 0, 0))
            draw.text((x, y), line_text, font=font_large, fill=(255, 255, 255))

        draw.text((640, 600), "SHORTS", font=font_small, fill=(255, 50, 50), anchor="mm")

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        img.save(output_path, quality=92)
        logger.info(f"Thumbnail saved: {output_path}")
        return output_path
