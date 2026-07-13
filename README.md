# 🌿 LeafScan — AI Plant Disease Detection

A full-stack web app that detects plant diseases from a leaf photo using AI,
and gives live weather-based farming advisories — all in a responsive,
interactive UI.

- **Backend:** Flask (Python)
- **AI model:** MobileNetV2 transfer-learning CNN (38 disease classes, 14 crops), trained on PlantVillage
- **Weather:** OpenWeatherMap API, converted into plain-language farming tips
- **Frontend:** HTML5, CSS3 (fully responsive, mobile nav, animations), vanilla JavaScript (no build step needed)

---

## 1. Project structure

```
plant-disease-detection/
├── app.py                     # Flask app: routes + API endpoints
├── requirements.txt
├── .env.example                # Copy to .env and add your weather API key
├── model/
│   ├── predict.py              # Loads trained model OR falls back to demo mode
│   ├── train_model.py          # Script to train the real CNN (transfer learning)
│   ├── treatments.py           # Remedy / prevention knowledge base
│   ├── labels.json              # 38 disease class definitions
│   └── plant_disease_model.h5  # (not included — created after you train)
├── templates/
│   ├── base.html               # Shared layout, nav, footer
│   ├── index.html              # Homepage
│   ├── detect.html             # Upload + AI diagnosis page
│   ├── weather.html            # Weather dashboard page
│   └── about.html
├── static/
│   ├── css/style.css           # Full design system, responsive breakpoints
│   ├── js/
│   │   ├── main.js             # Mobile nav toggle
│   │   ├── detect.js           # Upload, drag-drop, scan animation, results
│   │   └── weather.js          # Search, geolocation, weather rendering
│   └── uploads/                # Uploaded photos are saved here
└── data/                       # (you provide) training images go here
```

---

## 2. Quick start (demo mode — no ML training needed)

The app runs immediately out of the box using a lightweight heuristic
classifier, so you can see the entire UI and flow working before doing
any model training.

```bash
# 1. Clone / unzip the project, then enter the folder
cd plant-disease-detection

# 2. Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install the core dependencies (TensorFlow is optional at this stage)
pip install Flask Werkzeug python-dotenv requests numpy Pillow

# 4. Copy the environment file and (optionally) add a weather API key
cp .env.example .env
# then edit .env and paste your OpenWeatherMap key

# 5. Run the app
python app.py
```

Open **http://localhost:5000** in your browser. You'll see:
- **Home** — overview and hero
- **Detect** — upload a leaf photo and get an instant diagnosis
- **Weather** — search a city or use your location for live conditions + tips
- **About** — project/tech overview

> While no trained `.h5` model is present, the Detect page will show a
> "Demo mode" banner and use a simplified color-based heuristic instead of
> a real CNN. This lets the whole app work immediately; train the real
> model (step 3 below) whenever you're ready for genuine predictions.

---

## 3. Training the real AI model (optional but recommended)

1. **Download the dataset.** The PlantVillage dataset (colored, ~54,000 images,
   38 classes) is available on Kaggle:
   https://www.kaggle.com/datasets/abdallahalidev/plantvillage-dataset

2. **Arrange the folders** like this inside `data/`:
   ```
   data/
     train/
       Apple___Apple_scab/
       Apple___Black_rot/
       ... (one folder per class, images inside)
     val/
       Apple___Apple_scab/
       ...
   ```
   (An 80/20 train/val split of the original dataset works well.)

3. **Install TensorFlow** (skip this until you're ready to train — it's a large package):
   ```bash
   pip install tensorflow==2.16.1
   ```

4. **Run training:**
   ```bash
   python model/train_model.py --data_dir data --epochs 15 --fine_tune_epochs 5
   ```
   This trains a frozen-base MobileNetV2 head first, then fine-tunes the top
   layers. On a modest GPU this takes roughly 30–90 minutes; on CPU it will
   be considerably slower — reduce `--epochs` if you just want to test the
   pipeline.

5. **Restart the Flask app.** `model/predict.py` automatically detects
   `model/plant_disease_model.h5` and switches from demo mode to real
   predictions — no code changes needed.

> Tip: after training, check `model/class_indices.json` (auto-generated)
> against `model/labels.json` to make sure the class order lines up with
> your dataset's folder names.

---

## 4. Weather API setup

1. Create a free account at https://openweathermap.org/api
2. Generate an API key (free tier is enough — Current Weather + 5-day/3-hour Forecast)
3. Add it to your `.env` file:
   ```
   OPENWEATHER_API_KEY=your_key_here
   ```
4. Restart the app. The Weather page will now show live temperature,
   humidity, wind, a 5-day forecast, and rule-based farming tips
   (e.g. delaying spraying before rain, or flagging high humidity as a
   fungal-disease risk).

Without a key, the Weather page still renders correctly but shows a
notice explaining the key is missing.

---

## 5. Full package list

| Package | Purpose | Required? |
|---|---|---|
| Flask | Web server & routing | Yes |
| Werkzeug | Secure filename handling (Flask dependency) | Yes |
| python-dotenv | Loads `.env` config | Yes |
| requests | Calls the OpenWeatherMap API | Yes |
| numpy | Array/image math | Yes |
| Pillow | Image loading/resizing | Yes |
| tensorflow | Trains & runs the real CNN | Optional (demo mode works without it) |

Install everything (including TensorFlow) at once with:
```bash
pip install -r requirements.txt
```

---

## 6. Notes & next steps

- **Security:** this is a demo app — add authentication, file-type
  validation hardening, and rate limiting before deploying publicly.
- **Storage:** uploaded photos are saved to `static/uploads/`; consider
  clearing this periodically or moving to cloud storage (S3, GCS) in production.
- **Scaling the model:** you can swap MobileNetV2 for EfficientNet or a
  larger backbone in `train_model.py` if you have more compute available.
- **Deployment:** for production, run behind Gunicorn/uWSGI + Nginx, and
  set `debug=False` in `app.py`.

Enjoy scanning! 🍃
