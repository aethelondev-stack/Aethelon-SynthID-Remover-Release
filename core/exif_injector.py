import os
from datetime import datetime
from PIL import Image
import numpy as np
from typing import Optional, Dict

CAMERA_PRESETS = {
    "iphone12pro": {
        "name": "Apple iPhone 12 Pro",
        "make": "Apple",
        "model": "iPhone 12 Pro",
        "software": "17.5.1"
    },
    "iphone15pro": {
        "name": "Apple iPhone 15 Pro Max",
        "make": "Apple",
        "model": "iPhone 15 Pro Max",
        "software": "17.5.1"
    },
    "samsungs24": {
        "name": "Samsung Galaxy S24 Ultra",
        "make": "Samsung",
        "model": "SM-S928B",
        "software": "S928BXXU1AXB5"
    },
    "sonya7iv": {
        "name": "Sony Alpha 7 IV",
        "make": "Sony",
        "model": "ILCE-7M4",
        "software": "ILCE-7M4 v3.00"
    }
}

class ExifInjector:
    @staticmethod
    def save_with_exif(
        img_rgb: np.ndarray,
        output_path: str,
        preset: str = "iphone12pro",
        custom_date: Optional[str] = None,
        quality: int = 95
    ) -> str:
        """
        Saves an RGB image as a JPEG with authentic camera EXIF tags,
        stripping all C2PA and generative AI provenance metadata.
        """
        pil_img = Image.fromarray(img_rgb)
        exif = pil_img.getexif()

        preset_info = CAMERA_PRESETS.get(preset, CAMERA_PRESETS["iphone12pro"])
        date_str = custom_date or datetime.now().strftime("%Y:%m:%d %H:%M:%S")

        # 0x010F: Make
        exif[0x010F] = preset_info["make"]
        # 0x0110: Model
        exif[0x0110] = preset_info["model"]
        # 0x0131: Software
        exif[0x0131] = preset_info["software"]
        # 0x0132: DateTime
        exif[0x0132] = date_str

        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        pil_img.save(output_path, "JPEG", quality=quality, exif=exif, subsampling=1)
        return output_path
