# plugins/compress.py
from plugin_base import BasePlugin

try:
    from PIL import Image
except Exception:
    Image = None

class CompressPlugin(BasePlugin):
    PLUGIN_NAME = "compress"
    DESCRIPTION = "Compress (re-save) an image with given quality (1-95)."
    VERSION = "1.0.0"
    ENABLED_BY_DEFAULT = True

    def run(self, image_path: str, quality: int = 75):
        q = max(1, min(95, int(quality)))
        if Image:
            im = Image.open(image_path)
            out_path = f"{image_path.rsplit('.',1)[0]}_compressed.{image_path.rsplit('.',1)[1]}"
            im.save(out_path, quality=q, optimize=True)
            return {"status": "ok", "out_path": out_path}
        else:
            return {"status": "simulated", "message": f"Would compress {image_path} with quality={q}"}
