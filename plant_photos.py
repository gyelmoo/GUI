"""Plant pictures: read, save, replace and remove the optional photo of a plant."""

import os
import time

from config import (PLANT_PHOTO_DIR, PLANT_PHOTO_EXTENSIONS, PLANT_PHOTO_MAX_MB,
                    PLANT_PHOTO_SIZE)
from theme import PIL_OK

if PIL_OK:
    from PIL import Image, ImageOps


class PlantPhotoMixin:
    def plant_photo_path(self, filename):
        """Full path of a saved plant picture, or None if it is missing."""
        if not filename:
            return None
        path = os.path.join(PLANT_PHOTO_DIR, filename)
        return path if os.path.exists(path) else None

    def read_plant_photo(self, path):
        """Check and open a picture chosen by the user (not saved yet).

        Returns a PIL image. Raises ValueError with a friendly message if it cannot be used.
        """
        if not PIL_OK:
            raise ValueError("Plant pictures need the Pillow library.\n"
                             "Run:  pip install pillow   then restart the app.")
        if not path.lower().endswith(PLANT_PHOTO_EXTENSIONS):
            raise ValueError("Please choose a JPG or PNG picture.")
        try:
            too_big = os.path.getsize(path) > PLANT_PHOTO_MAX_MB * 1024 * 1024
        except OSError:
            too_big = False
        if too_big:
            raise ValueError(f"Please choose a picture smaller than {PLANT_PHOTO_MAX_MB} MB.")
        try:
            with Image.open(path) as src:
                img = ImageOps.exif_transpose(src).convert("RGB")
        except Exception:
            raise ValueError("That file could not be opened as a picture. Try a JPG or PNG.")
        img.thumbnail((PLANT_PHOTO_SIZE, PLANT_PHOTO_SIZE), Image.LANCZOS)
        return img

    def store_plant_photo(self, plant_id, img, old_filename=None):
        """Save the picture for this plant and remember it in the database."""
        os.makedirs(PLANT_PHOTO_DIR, exist_ok=True)
        safe_id = "".join(c for c in plant_id.lower() if c.isalnum() or c in "-_")
        name = f"user{self.user['id']}_{safe_id}_{int(time.time() * 1000)}.jpg"
        img.convert("RGB").save(os.path.join(PLANT_PHOTO_DIR, name), quality=90)
        self.db.set_plant_photo(self.user["id"], plant_id, name)
        self._delete_photo_file(old_filename)
        return name

    def remove_plant_photo(self, plant_id, old_filename):
        self.db.set_plant_photo(self.user["id"], plant_id, None)
        self._delete_photo_file(old_filename)

    @staticmethod
    def _delete_photo_file(filename):
        if not filename:
            return
        path = os.path.join(PLANT_PHOTO_DIR, filename)
        try:
            if os.path.exists(path):
                os.remove(path)
        except OSError:
            pass
