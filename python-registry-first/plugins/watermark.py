# plugins/watermark.py
from plugin_base import BasePlugin

try:
    from PIL import Image, ImageDraw, ImageFont
except Exception:
    Image = ImageDraw = ImageFont = None

class WatermarkPlugin(BasePlugin):
    PLUGIN_NAME = "watermark"
    DESCRIPTION = "Apply a text watermark to the bottom-right of an image."
    VERSION = "0.9.0"
    ENABLED_BY_DEFAULT = True

    def run(self, image_path: str, text: str = "© MyApp"):
        if Image and ImageDraw:
            im = Image.open(image_path).convert("RGBA")
            txt_layer = Image.new("RGBA", im.size, (255,255,255,0))
            draw = ImageDraw.Draw(txt_layer)
            # fallback font
            try:
                font = ImageFont.truetype("arial.ttf", 16)
            except Exception:
                font = ImageFont.load_default()
            margin = 10
            w, h = draw.textsize(text, font=font)
            pos = (im.width - w - margin, im.height - h - margin)
            draw.text(pos, text, fill=(255,255,255,150), font=font)
            out = Image.alpha_composite(im, txt_layer).convert("RGB")
            out_path = f"{image_path.rsplit('.',1)[0]}_wm.{image_path.rsplit('.',1)[1]}"
            out.save(out_path)
            return {"status": "ok", "out_path": out_path}
        else:
            return {"status": "simulated", "message": f"Would watermark {image_path} with '{text}'"}
