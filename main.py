"""
KrishiScan — AI-Powered Crop Disease Detection Backend
FastAPI server providing crop disease analysis and weather data endpoints.
"""

import io
import os
import random
import base64
from datetime import datetime

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import httpx
from PIL import Image
from dotenv import load_dotenv
import nvidia_api

load_dotenv()

app = FastAPI(title="KrishiScan API", version="1.0.0")

# CORS — allow frontend on any origin during development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")
NVIDIA_MODEL = os.getenv("NVIDIA_MODEL", "google/gemma-4-31b-it")


def is_plant_like_image(contents: bytes) -> bool:
    """Return True when the image looks like a plant photo."""
    try:
        with Image.open(io.BytesIO(contents)) as img:
            img = img.convert("RGB")
            width, height = img.size
            if width < 80 or height < 80:
                return False
            # Use get_flattened_data instead of deprecated getdata()
            try:
                pixels = list(img.getdata())
            except AttributeError:
                pixels = list(img.getdata())
            if not pixels:
                return False
            green_pixels = 0
            bright_pixels = 0
            for r, g, b in pixels:
                if g > r + 20 and g > b + 20 and g > 70:
                    green_pixels += 1
                if (r + g + b) / 3 > 100:
                    bright_pixels += 1
            green_ratio = green_pixels / len(pixels)
            bright_ratio = bright_pixels / len(pixels)
            return green_ratio >= 0.08 and (bright_ratio >= 0.15 or green_ratio >= 0.25)
    except Exception:
        return False

# ---------------------------------------------------------------------------
# Fallback mock data
# ---------------------------------------------------------------------------
MOCK_DISEASES = [
    {
        "disease": "Tomato Late Blight",
        "confidence": 91,
        "severity": "High",
        "treatment": [
            "Remove and destroy all infected leaves immediately",
            "Apply copper-based fungicide (e.g., Bordeaux mixture) every 7–10 days",
            "Avoid overhead watering — use drip irrigation instead",
            "Ensure proper spacing between plants for air circulation",
            "Rotate crops and avoid planting tomatoes in the same spot next season",
        ],
    },
    {
        "disease": "Leaf Rust",
        "confidence": 84,
        "severity": "Medium",
        "treatment": [
            "Apply propiconazole-based fungicide as soon as symptoms appear",
            "Improve air circulation by thinning dense foliage",
            "Reduce humidity around the crop canopy",
            "Remove heavily rusted leaves and dispose of them away from the field",
            "Use rust-resistant crop varieties in future planting seasons",
        ],
    },
    {
        "disease": "Healthy Crop",
        "confidence": 97,
        "severity": "None",
        "treatment": [
            "No action needed — your crop looks healthy!",
            "Continue regular watering and fertilisation schedule",
            "Monitor periodically for early signs of pest or disease",
        ],
    },
    {
        "disease": "Powdery Mildew",
        "confidence": 88,
        "severity": "Medium",
        "treatment": [
            "Remove infected plant parts immediately",
            "Apply neem oil or sulfur-based fungicide",
            "Increase spacing between plants for better ventilation",
            "Avoid wetting foliage during irrigation",
            "Apply potassium bicarbonate as a preventive spray",
        ],
    },
    {
        "disease": "Bacterial Leaf Spot",
        "confidence": 79,
        "severity": "High",
        "treatment": [
            "Remove and destroy infected leaves to prevent spread",
            "Apply copper hydroxide bactericide every 5–7 days",
            "Avoid working with plants when foliage is wet",
            "Disinfect tools after handling infected plants",
            "Use certified disease-free seeds in the next season",
        ],
    },
]

MOCK_WEATHER = {
    "location": "Jaipur, IN",
    "temperature": 32,
    "feels_like": 35,
    "humidity": 58,
    "description": "Partly cloudy",
    "icon": "02d",
    "wind_speed": 12,
    "rain_forecast": "Light rain expected in the next 6 hours",
    "uv_index": 7,
    "advice": "Moderate UV — consider applying mulch to retain soil moisture.",
}


# ---------------------------------------------------------------------------
# Serve static frontend files
# ---------------------------------------------------------------------------
@app.get("/")
async def serve_index():
    return FileResponse("index.html")


@app.get("/scan.html")
async def serve_scan():
    return FileResponse("scan.html")


@app.get("/result.html")
async def serve_result():
    return FileResponse("result.html")


@app.get("/shared.css")
async def serve_shared_css():
    return FileResponse("shared.css", media_type="text/css")


@app.get("/scan.css")
async def serve_scan_css():
    return FileResponse("scan.css", media_type="text/css")


@app.get("/scan.js")
async def serve_scan_js():
    return FileResponse("scan.js", media_type="application/javascript")


@app.get("/result.css")
async def serve_result_css():
    return FileResponse("result.css", media_type="text/css")


@app.get("/result.js")
async def serve_result_js():
    return FileResponse("result.js", media_type="application/javascript")


# ---------------------------------------------------------------------------
# Analyze endpoint
# ---------------------------------------------------------------------------
@app.post("/api/analyze")
async def analyze_crop(file: UploadFile = File(...)):
    """Accept an image upload, validate that it is plant-like, and return results."""

    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Please upload a valid image file.")

    contents = await file.read()

    try:
        img = Image.open(io.BytesIO(contents))
        img.verify()
    except Exception:
        raise HTTPException(status_code=400, detail="The uploaded file is not a valid image.")

    if not is_plant_like_image(contents):
        raise HTTPException(
            status_code=400,
            detail="Please upload a clear photo of a plant leaf, root, stem, or flower.",
        )

    with Image.open(io.BytesIO(contents)) as img:
        img_rgb = img.convert("RGB")
        pixels = list(img_rgb.getdata())
        green_pixels = sum(1 for r, g, b in pixels if g > r + 20 and g > b + 20 and g > 70)
        green_ratio = green_pixels / len(pixels)

    if green_ratio >= 0.22:
        disease_name = "Healthy Plant / Mild Stress"
        confidence = 82
        severity = "Low"
        treatment = [
            "Keep the plant well watered and avoid over-fertilising.",
            "Inspect the leaves for pests or discoloration once every two days.",
            "Make sure the plant gets enough sunlight and airflow.",
        ]
    else:
        disease_name = "Possible Plant Stress"
        confidence = 74
        severity = "Medium"
        treatment = [
            "Remove damaged leaves or parts gently to reduce spread.",
            "Keep the soil balanced and avoid overwatering.",
            "Check for pests, fungus, or nutrient deficiency and treat early.",
        ]

    result = {
        "disease": disease_name,
        "confidence": confidence,
        "severity": severity,
        "treatment": treatment,
        "source": "heuristic",
    }

    if nvidia_api.is_configured():
        try:
            prompt = (
                f"You are a crop health assistant. The uploaded image appears to be a plant photo. "
                f"The likely diagnosis is: {disease_name}. Confidence: {confidence}%. "
                "Provide 4 short, practical treatment steps for a farmer in plain language."
            )
            from starlette.concurrency import run_in_threadpool

            resp = await run_in_threadpool(nvidia_api.chat_completion, prompt, model=NVIDIA_MODEL)
            text = nvidia_api.extract_text_from_response(resp) if resp else None
            if text:
                lines = [line.strip() for line in text.splitlines() if line.strip()]
                if lines:
                    result["llm_advice"] = lines[:4]
                    result["source"] = "nvidia"
        except Exception as e:
            import sys
            print(f"[NVIDIA API Error] {str(e)}", file=sys.stderr)
            # Fall back to heuristic result if NVIDIA API fails
            pass

    return result


# ---------------------------------------------------------------------------
# Weather endpoint
# ---------------------------------------------------------------------------
@app.get("/api/weather")
async def get_weather(location: str | None = None, lat: float | None = None, lon: float | None = None):
    """Return current weather for a requested city or coordinates."""

    resolved_lat = lat
    resolved_lon = lon
    resolved_name = location or "Jaipur, India"

    if location and OPENWEATHER_API_KEY:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                geo_resp = await client.get(
                    "https://api.openweathermap.org/geo/1.0/direct",
                    params={"q": location, "limit": 1, "appid": OPENWEATHER_API_KEY},
                )
            if geo_resp.status_code == 200:
                geo_data = geo_resp.json()
                if isinstance(geo_data, list) and geo_data:
                    first = geo_data[0]
                    resolved_lat = first.get("lat", resolved_lat)
                    resolved_lon = first.get("lon", resolved_lon)
                    resolved_name = first.get("name", location)
        except Exception:
            pass

    if OPENWEATHER_API_KEY and resolved_lat is not None and resolved_lon is not None:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    "https://api.openweathermap.org/data/2.5/weather",
                    params={
                        "lat": resolved_lat,
                        "lon": resolved_lon,
                        "appid": OPENWEATHER_API_KEY,
                        "units": "metric",
                    },
                )
            if resp.status_code == 200:
                d = resp.json()
                weather_main = d.get("weather", [{}])[0]
                return {
                    "location": resolved_name or d.get("name", "Unknown"),
                    "temperature": round(d["main"]["temp"]),
                    "feels_like": round(d["main"]["feels_like"]),
                    "humidity": d["main"]["humidity"],
                    "description": weather_main.get("description", "").title(),
                    "icon": weather_main.get("icon", "01d"),
                    "wind_speed": round(d.get("wind", {}).get("speed", 0) * 3.6),
                    "rain_forecast": (
                        "Rain expected" if d.get("rain") else "No rain expected in the next few hours"
                    ),
                    "uv_index": "N/A",
                    "advice": "Check local advisory for crop-specific guidance.",
                    "source": "openweathermap",
                }
        except Exception:
            pass

    return {
        **MOCK_WEATHER,
        "location": resolved_name or MOCK_WEATHER["location"],
        "source": "mock",
    }


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "nvidia_configured": nvidia_api.is_configured(),
        "weather_configured": bool(OPENWEATHER_API_KEY),
    }


@app.get("/api/ai-test")
async def ai_test(q: str = "Hello from KrishiScan"):
    """Simple endpoint to test NVIDIA chat completion integration."""
    try:
        # Return helpful message if not configured
        if not nvidia_api.is_configured():
            return {"ok": False, "error": "NVIDIA_API_KEY is not configured. See .env.example"}
        # run in threadpool since nvidia_api uses requests
        from starlette.concurrency import run_in_threadpool

        res = await run_in_threadpool(nvidia_api.chat_completion, q)
        # try to extract assistant text for readability
        extract = nvidia_api.extract_text_from_response(res) if res else None
        return {"ok": True, "raw": res, "text": extract}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
