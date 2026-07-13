"""
Plant Disease Detection - Flask Backend
=========================================
Serves the web app, handles image uploads for AI disease detection,
and proxies live weather data for farm-planning decisions.
"""

import os
import io
import uuid
import time
from datetime import datetime, timezone

import requests
import numpy as np
from PIL import Image
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

from model.predict import PlantDiseaseDetector
from flask import redirect, url_for, flash   # add these to your existing "from flask import ..." line
from flask_login import LoginManager, login_user, logout_user, login_required, current_user

from model.fertilizer import recommend_fertilizer, recommend_for_disease, CROP_REQUIREMENTS
from model.price_predictor import PricePredictor
from models import db, Farmer, ScanHistory
load_dotenv()

# ------------------------------------------------------------------
# Configuration
# ------------------------------------------------------------------
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
MAX_CONTENT_LENGTH = 8 * 1024 * 1024  # 8 MB

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")
OPENWEATHER_BASE = "https://api.openweathermap.org/data/2.5"
OPENWEATHER_GEO = "https://api.openweathermap.org/geo/1.0"

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key-change-this-in-production")
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{os.path.join(BASE_DIR, 'leafscan.db')}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login_page"
login_manager.login_message = "Please log in to scan a leaf and get fertilizer advice."
login_manager.login_message_category = "info"


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(Farmer, int(user_id))


with app.app_context():
    db.create_all()
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Load the AI model once at startup (falls back to a heuristic demo
# mode automatically if no trained .h5 file is found — see model/predict.py)
detector = PlantDiseaseDetector(
    model_path=os.path.join(BASE_DIR, "model", "plant_disease_model.h5"),
    labels_path=os.path.join(BASE_DIR, "model", "labels.json"),
)

price_predictor = PricePredictor(
    model_path=os.path.join(BASE_DIR, "model", "price_model.pkl"),
    crops_path=os.path.join(BASE_DIR, "model", "price_crops.json"),
    fallback_csv_path=os.path.join(BASE_DIR, "data", "crop_prices_sample.csv"),
)


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# ------------------------------------------------------------------
# Page routes
# ------------------------------------------------------------------
@app.route("/")
def home():
    return render_template("index.html", active="home")


@app.route("/detect")
@login_required
def detect_page():
    return render_template("detect.html", active="detect")


@app.route("/weather")
def weather_page():
    return render_template("weather.html", active="weather", has_key=bool(OPENWEATHER_API_KEY))


@app.route("/about")
def about_page():
    return render_template("about.html", active="about")

@app.route("/fertilizer")
@login_required
def fertilizer_page():
    crops = sorted(k for k in CROP_REQUIREMENTS.keys() if k != "default")
    return render_template("fertilizer.html", active="fertilizer", crops=crops)


@app.route("/price")
@login_required
def price_page():
    crops = price_predictor.available_crops()
    return render_template("price.html", active="price", crops=crops)


@app.route("/dashboard")
@login_required
def dashboard_page():
    scans = ScanHistory.query.filter_by(farmer_id=current_user.id) \
        .order_by(ScanHistory.created_at.desc()).limit(20).all()
    return render_template("dashboard.html", active="dashboard", scans=scans)


@app.route("/scans/<int:scan_id>/delete", methods=["POST"])
@login_required
def delete_scan(scan_id):
    scan = ScanHistory.query.get_or_404(scan_id)
    if scan.farmer_id != current_user.id:
        flash("You don't have permission to delete that scan.", "error")
        return redirect(url_for("dashboard_page"))
    db.session.delete(scan)
    db.session.commit()
    flash("Scan deleted.", "success")
    return redirect(url_for("dashboard_page"))


@app.route("/scans/clear-all", methods=["POST"])
@login_required
def clear_all_scans():
    ScanHistory.query.filter_by(farmer_id=current_user.id).delete()
    db.session.commit()
    flash("All scan history cleared.", "success")
    return redirect(url_for("dashboard_page"))


@app.route("/register", methods=["GET", "POST"])
def register_page():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard_page"))
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        location = request.form.get("location", "").strip()
        if not name or not email or not password:
            flash("Name, email and password are all required.", "error")
            return render_template("register.html", active="register")
        if len(password) < 6:
            flash("Password must be at least 6 characters.", "error")
            return render_template("register.html", active="register")
        if Farmer.query.filter_by(email=email).first():
            flash("An account with that email already exists. Try logging in instead.", "error")
            return render_template("register.html", active="register")
        farmer = Farmer(name=name, email=email, location=location or None)
        farmer.set_password(password)
        db.session.add(farmer)
        db.session.commit()
        login_user(farmer)
        flash(f"Welcome, {farmer.name}! Your account is ready.", "success")
        return redirect(url_for("dashboard_page"))
    return render_template("register.html", active="register")


@app.route("/login", methods=["GET", "POST"])
def login_page():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard_page"))
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        farmer = Farmer.query.filter_by(email=email).first()
        if farmer is None or not farmer.check_password(password):
            flash("Incorrect email or password.", "error")
            return render_template("login.html", active="login")
        login_user(farmer)
        flash(f"Welcome back, {farmer.name}!", "success")
        return redirect(url_for("dashboard_page"))
    return render_template("login.html", active="login")


@app.route("/logout")
@login_required
def logout_page():
    logout_user()
    flash("You've been logged out.", "info")
    return redirect(url_for("home"))


# ------------------------------------------------------------------
# API: Disease Detection
# ------------------------------------------------------------------
@app.route("/api/predict", methods=["POST"])
@login_required
def api_predict():
    if "image" not in request.files:
        return jsonify({"error": "No image file provided."}), 400

    file = request.files["image"]
    if file.filename == "":
        return jsonify({"error": "No file selected."}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "Unsupported file type. Use JPG, PNG or WEBP."}), 400

    try:
        img_bytes = file.read()
        image = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    except Exception:
        return jsonify({"error": "Could not read image. The file may be corrupted."}), 400

    # Save a copy for the results gallery / history
    filename = f"{uuid.uuid4().hex[:10]}_{secure_filename(file.filename)}"
    save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    image.save(save_path, quality=85)

    start = time.time()
    result = detector.predict(image)
    elapsed_ms = round((time.time() - start) * 1000, 1)

    result.update({
        "image_url": f"/static/uploads/{filename}",
        "inference_ms": elapsed_ms,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "demo_mode": detector.demo_mode,
    })
    fertilizer_tip = recommend_for_disease(result["plant"], result["status"], result["severity"])
    result["fertilizer_tip"] = fertilizer_tip

    scan = ScanHistory(
        farmer_id=current_user.id,
        plant=result["plant"],
        label=result["label"],
        status=result["status"],
        severity=result["severity"],
        confidence=result["confidence"],
        image_url=result["image_url"],
        fertilizer_summary=fertilizer_tip.get("summary", ""),
    )
    db.session.add(scan)
    db.session.commit()
    return jsonify(result)

@app.route("/api/fertilizer-recommend", methods=["POST"])
@login_required
def api_fertilizer_recommend():
    data = request.get_json(silent=True) or {}
    crop = data.get("crop", "").strip()
    try:
        n = float(data.get("n"))
        p = float(data.get("p"))
        k = float(data.get("k"))
        ph = float(data.get("ph"))
    except (TypeError, ValueError):
        return jsonify({"error": "Please provide numeric values for N, P, K and pH."}), 400
    if not crop:
        return jsonify({"error": "Please select a crop."}), 400
    if not (0 <= ph <= 14):
        return jsonify({"error": "pH must be between 0 and 14."}), 400
    result = recommend_fertilizer(crop, n, p, k, ph)
    return jsonify(result)


@app.route("/api/price-predict", methods=["POST"])
@login_required
def api_price_predict():
    data = request.get_json(silent=True) or {}
    crop = data.get("crop", "").strip()

    try:
        month = int(data.get("month"))
        year = int(data.get("year"))
    except (TypeError, ValueError):
        return jsonify({"error": "Please provide a valid month and year."}), 400

    if not crop:
        return jsonify({"error": "Please select a crop."}), 400
    if not (1 <= month <= 12):
        return jsonify({"error": "Month must be between 1 and 12."}), 400

    try:
        result = price_predictor.predict(crop, month, year)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    return jsonify(result)
# ------------------------------------------------------------------
# API: Weather
# ------------------------------------------------------------------
@app.route("/api/weather")
def api_weather():
    city = request.args.get("city", "").strip()
    lat = request.args.get("lat")
    lon = request.args.get("lon")

    if not OPENWEATHER_API_KEY:
        return jsonify({"error": "no_api_key",
                         "message": "Add OPENWEATHER_API_KEY to your .env file to enable live weather."}), 200

    try:
        if lat and lon:
            params = {"lat": lat, "lon": lon, "appid": OPENWEATHER_API_KEY, "units": "metric"}
        elif city:
            params = {"q": city, "appid": OPENWEATHER_API_KEY, "units": "metric"}
        else:
            return jsonify({"error": "missing_params", "message": "Provide a city name or coordinates."}), 400

        current = requests.get(f"{OPENWEATHER_BASE}/weather", params=params, timeout=8)
        if current.status_code != 200:
            return jsonify({"error": "not_found",
                             "message": current.json().get("message", "Location not found.")}), 200
        current_data = current.json()

        forecast = requests.get(f"{OPENWEATHER_BASE}/forecast", params=params, timeout=8)
        forecast_data = forecast.json() if forecast.status_code == 200 else {"list": []}

        daily = _summarize_forecast(forecast_data.get("list", []))
        tips = _farming_tips(current_data, daily)

        return jsonify({
            "location": {
                "name": current_data.get("name"),
                "country": current_data.get("sys", {}).get("country"),
                "lat": current_data.get("coord", {}).get("lat"),
                "lon": current_data.get("coord", {}).get("lon"),
            },
            "current": {
                "temp": current_data["main"]["temp"],
                "feels_like": current_data["main"]["feels_like"],
                "humidity": current_data["main"]["humidity"],
                "pressure": current_data["main"]["pressure"],
                "wind_speed": current_data["wind"]["speed"],
                "condition": current_data["weather"][0]["main"],
                "description": current_data["weather"][0]["description"],
                "icon": current_data["weather"][0]["icon"],
                "clouds": current_data.get("clouds", {}).get("all"),
                "sunrise": current_data["sys"]["sunrise"],
                "sunset": current_data["sys"]["sunset"],
            },
            "daily_forecast": daily,
            "farming_tips": tips,
        })
    except requests.exceptions.RequestException as exc:
        return jsonify({"error": "network_error", "message": str(exc)}), 200


def _summarize_forecast(entries):
    """Collapse OpenWeather's 3-hour forecast list into a 5-day daily summary."""
    days = {}
    for entry in entries:
        date = entry["dt_txt"].split(" ")[0]
        days.setdefault(date, []).append(entry)

    summary = []
    for date, items in list(days.items())[:5]:
        temps = [i["main"]["temp"] for i in items]
        pops = [i.get("pop", 0) for i in items]
        mid = items[len(items) // 2]
        summary.append({
            "date": date,
            "temp_min": round(min(temps), 1),
            "temp_max": round(max(temps), 1),
            "rain_chance": round(max(pops) * 100),
            "condition": mid["weather"][0]["main"],
            "icon": mid["weather"][0]["icon"],
        })
    return summary


def _farming_tips(current, daily):
    """Simple rule-based agro-advisory derived from live conditions."""
    tips = []
    humidity = current["main"]["humidity"]
    temp = current["main"]["temp"]
    wind = current["wind"]["speed"]
    condition = current["weather"][0]["main"].lower()

    if humidity >= 80:
        tips.append({
            "type": "warning",
            "text": "High humidity detected — fungal diseases like blight and mildew spread "
                    "faster in these conditions. Inspect crops closely over the next few days.",
        })
    if any(d["rain_chance"] >= 60 for d in daily[:2]):
        tips.append({
            "type": "info",
            "text": "Rain likely in the next 48 hours. Consider delaying fungicide spraying "
                    "since rain can wash off treatments before they take effect.",
        })
    if temp >= 35:
        tips.append({
            "type": "warning",
            "text": "High temperatures may stress plants. Water early morning or evening to "
                    "reduce evaporation loss.",
        })
    if wind >= 8:
        tips.append({
            "type": "info",
            "text": "Windy conditions — avoid spraying pesticides or fertilizers now to prevent drift.",
        })
    if "clear" in condition and humidity < 50:
        tips.append({
            "type": "success",
            "text": "Clear, dry conditions are favorable for field work, pruning, and spraying today.",
        })
    if not tips:
        tips.append({
            "type": "success",
            "text": "Conditions look stable. Continue with your regular crop monitoring routine.",
        })
    return tips


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(debug=os.getenv("FLASK_DEBUG", "0") == "1", host="0.0.0.0", port=port)