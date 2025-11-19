# plugins/resize.py
from plugin_base import BasePlugin

try:
    from PIL import Image
except Exception:
    Image = None  # fallback to simulated behavior if Pillow isn't installed

class ResizePlugin(BasePlugin):
    PLUGIN_NAME = "resize"
    DESCRIPTION = "Resize an image to width x height (pixels)."
    VERSION = "1.0.0"

    def run(self, image_path: str, width: int, height: int):
        if Image:
            im = Image.open(image_path)
            im2 = im.resize((int(width), int(height)))
            out_path = f"{image_path.rsplit('.',1)[0]}_resized.{image_path.rsplit('.',1)[1]}"
            im2.save(out_path)
            return {"status": "ok", "out_path": out_path}
        else:
            # fallback (no real image ops)
            return {"status": "simulated", "message": f"Would resize {image_path} to {width}x{height}"}
