"""Uploaded-image processing with Pillow.

Downscales to a sensible max dimension, honours EXIF orientation, flattens
transparency onto white, and re-encodes as optimised progressive JPEG — so a
10 MB phone photo lands as a ~100–300 KB web image. Returns the stored filename.
"""

from __future__ import annotations

import os
import uuid

from flask import current_app
from PIL import Image, ImageOps

MAX_DIM = 1600      # longest side, px
JPEG_QUALITY = 82


def process_upload(file_storage) -> str:
    try:
        img = Image.open(file_storage.stream)
        img.load()
    except Exception as exc:  # noqa: BLE001 - anything Pillow can't open isn't an image
        raise ValueError("الملف ليس صورة صالحة") from exc

    img = ImageOps.exif_transpose(img)          # rotate per camera orientation
    img.thumbnail((MAX_DIM, MAX_DIM))            # shrink only, keep aspect ratio

    if img.mode in ("RGBA", "LA", "P"):
        rgba = img.convert("RGBA")
        flat = Image.new("RGB", rgba.size, (255, 255, 255))
        flat.paste(rgba, mask=rgba.split()[-1])
        img = flat
    else:
        img = img.convert("RGB")

    folder = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(folder, exist_ok=True)
    name = f"{uuid.uuid4().hex}.jpg"
    img.save(os.path.join(folder, name), "JPEG",
             quality=JPEG_QUALITY, optimize=True, progressive=True)
    return name
