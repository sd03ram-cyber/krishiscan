import io
import unittest
from PIL import Image

from main import is_plant_like_image


class PlantImageValidationTests(unittest.TestCase):
    def test_green_leaf_like_image_is_accepted(self):
        image = Image.new("RGB", (120, 120), color=(20, 140, 30))
        buf = io.BytesIO()
        image.save(buf, format="PNG")
        self.assertTrue(is_plant_like_image(buf.getvalue()))

    def test_colourful_non_plant_image_is_rejected(self):
        image = Image.new("RGB", (120, 120), color=(255, 0, 0))
        buf = io.BytesIO()
        image.save(buf, format="PNG")
        self.assertFalse(is_plant_like_image(buf.getvalue()))


if __name__ == "__main__":
    unittest.main()
