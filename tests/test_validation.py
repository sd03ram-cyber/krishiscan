import asyncio
import io
import unittest
from unittest.mock import AsyncMock, patch
from PIL import Image

from main import get_weather, is_plant_like_image


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


class WeatherLocationTests(unittest.TestCase):
    def test_weather_uses_location_query_when_provided(self):
        class FakeResponse:
            def __init__(self, payload, status_code=200):
                self._payload = payload
                self.status_code = status_code

            def json(self):
                return self._payload

        async def run_test():
            with patch("main.httpx.AsyncClient") as client_cls, patch("main.OPENWEATHER_API_KEY", "demo-key"):
                client = AsyncMock()
                client_cls.return_value.__aenter__.return_value = client
                client.get = AsyncMock(
                    side_effect=[
                        FakeResponse([
                            {"name": "Delhi", "lat": 28.61, "lon": 77.23}
                        ]),
                        FakeResponse({
                            "name": "Delhi",
                            "main": {"temp": 31, "feels_like": 33, "humidity": 62},
                            "weather": [{"description": "clear sky", "icon": "01d"}],
                            "wind": {"speed": 2.5},
                        }),
                    ]
                )
                result = await get_weather(location="Delhi")
                self.assertEqual(result["location"], "Delhi")
                self.assertEqual(result["source"], "openweathermap")
                first_call = client.get.await_args_list[0]
                self.assertEqual(first_call.kwargs["params"]["q"], "Delhi")

        asyncio.run(run_test())


if __name__ == "__main__":
    unittest.main()
