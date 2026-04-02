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
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import httpx
from PIL import Image

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
ROBOFLOW_API_KEY = os.getenv("ROBOFLOW_API_KEY", "")
ROBOFLOW_MODEL = os.getenv("ROBOFLOW_MODEL", "plant-disease-detection-nkbjm/1")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")

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
    """Accept an image upload, run disease detection, return results."""

    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Please upload a valid image file.")

    contents = await file.read()

    # Validate image
    try:
        img = Image.open(io.BytesIO(contents))
        img.verify()
    except Exception:
        raise HTTPException(status_code=400, detail="The uploaded file is not a valid image.")

    # --- Try Roboflow inference ---
    if ROBOFLOW_API_KEY:
        try:
            img_b64 = base64.b64encode(contents).decode("utf-8")
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    f"https://detect.roboflow.com/{ROBOFLOW_MODEL}",
                    params={"api_key": ROBOFLOW_API_KEY},
                    json={"image": img_b64},
                )
            if resp.status_code == 200:
                data = resp.json()
                predictions = data.get("predictions", [])
                if predictions:
                    top = max(predictions, key=lambda p: p.get("confidence", 0))
                    disease_name = top.get("class", "Unknown Disease")
                    confidence = round(top.get("confidence", 0) * 100)
                    severity = (
                        "High" if confidence >= 85
                        else "Medium" if confidence >= 60
                        else "Low"
                    )
                    return {
                        "disease": disease_name,
                        "confidence": confidence,
                        "severity": severity,
                        "treatment": [
                            f"Detected: {disease_name}. Consult a local agronomist for tailored advice.",
                            "Remove visibly affected plant parts to limit spread.",
                            "Apply an appropriate fungicide or pesticide after expert consultation.",
                            "Ensure adequate spacing and ventilation around plants.",
                            "Monitor crop closely over the next 7 days and scan again.",
                        ],
                        "source": "roboflow",
                    }
        except Exception:
            pass  # fall through to mock

    # --- Fallback to mock ---
    result = random.choice(MOCK_DISEASES)
    return {**result, "source": "mock"}


# ---------------------------------------------------------------------------
# Weather endpoint
# ---------------------------------------------------------------------------
@app.get("/api/weather")
async def get_weather(lat: float = 26.9124, lon: float = 75.7873):
    """Return current weather. Defaults to Jaipur, India."""

    if OPENWEATHER_API_KEY:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    "https://api.openweathermap.org/data/2.5/weather",
                    params={
                        "lat": lat,
                        "lon": lon,
                        "appid": OPENWEATHER_API_KEY,
                        "units": "metric",
                    },
                )
            if resp.status_code == 200:
                d = resp.json()
                weather_main = d.get("weather", [{}])[0]
                return {
                    "location": d.get("name", "Unknown"),
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

    return {**MOCK_WEATHER, "source": "mock"}


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "roboflow_configured": bool(ROBOFLOW_API_KEY),
        "weather_configured": bool(OPENWEATHER_API_KEY),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
