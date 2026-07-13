"""
price_predictor.py
====================
Wraps the trained crop price regression model and exposes a single
`.predict(crop, month, year)` method. If no trained model file is found,
falls back to a simple seasonal-average heuristic computed directly from
the sample CSV, so the feature still works even before training is run.
"""

import json
import os

import joblib
import pandas as pd

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
FEATURE_COLUMNS = ["crop_idx", "month", "time_idx"]


class PricePredictor:
    def __init__(self, model_path, crops_path, fallback_csv_path):
        self.model_path = model_path
        self.fallback_csv_path = fallback_csv_path
        self.model_bundle = None
        self.crops = []
        self.demo_mode = True
        self._fallback_df = None

        if os.path.exists(model_path) and os.path.exists(crops_path):
            try:
                self.model_bundle = joblib.load(model_path)
                with open(crops_path) as f:
                    self.crops = json.load(f)
                self.demo_mode = False
                print(f"[PricePredictor] Loaded trained model from {model_path}")
            except Exception as exc:
                print(f"[PricePredictor] Could not load model ({exc}); using seasonal-average fallback.")

        if self.demo_mode:
            print(f"[PricePredictor] No trained model found at {model_path}. "
                  f"Using a seasonal-average heuristic from {fallback_csv_path}. "
                  f"Run model/train_price_model.py to train the real regression model.")
            if os.path.exists(fallback_csv_path):
                self._fallback_df = pd.read_csv(fallback_csv_path)
                self.crops = sorted(self._fallback_df["crop"].unique().tolist())

    def available_crops(self):
        return self.crops

    def predict(self, crop: str, month: int, year: int) -> dict:
        if crop not in self.crops:
            raise ValueError(f"Unknown crop '{crop}'. Available crops: {', '.join(self.crops)}")

        if not self.demo_mode:
            return self._predict_with_model(crop, month, year)
        return self._predict_heuristic(crop, month)

    def _predict_with_model(self, crop, month, year) -> dict:
        model = self.model_bundle["model"]
        crop_to_idx = self.model_bundle["crop_to_idx"]
        min_year = self.model_bundle["min_year"]

        crop_idx = crop_to_idx[crop]
        time_idx = (year - min_year) * 12 + month

        input_row = pd.DataFrame([[crop_idx, month, time_idx]], columns=FEATURE_COLUMNS)
        pred = model.predict(input_row)[0]

        # Build a simple 3-month-ahead trend so the UI can show a mini forecast
        trend = []
        for offset in range(0, 4):
            m = ((month - 1 + offset) % 12) + 1
            y = year + ((month - 1 + offset) // 12)
            t_idx = (y - min_year) * 12 + m
            row = pd.DataFrame([[crop_idx, m, t_idx]], columns=FEATURE_COLUMNS)
            p = model.predict(row)[0]
            trend.append({"month": m, "year": y, "price": round(float(p), 2)})

        return {
            "crop": crop,
            "predicted_price": round(float(pred), 2),
            "unit": "INR per quintal",
            "trend": trend,
            "demo_mode": False,
        }

    def _predict_heuristic(self, crop, month) -> dict:
        """Fallback: average historical price for this crop+month from the sample CSV."""
        subset = self._fallback_df[(self._fallback_df["crop"] == crop) & (self._fallback_df["month"] == month)]
        if subset.empty:
            subset = self._fallback_df[self._fallback_df["crop"] == crop]
        avg_price = float(subset["price_per_quintal_inr"].mean())

        trend = []
        for offset in range(0, 4):
            m = ((month - 1 + offset) % 12) + 1
            sub = self._fallback_df[(self._fallback_df["crop"] == crop) & (self._fallback_df["month"] == m)]
            p = float(sub["price_per_quintal_inr"].mean()) if not sub.empty else avg_price
            trend.append({"month": m, "year": None, "price": round(p, 2)})

        return {
            "crop": crop,
            "predicted_price": round(avg_price, 2),
            "unit": "INR per quintal",
            "trend": trend,
            "demo_mode": True,
        }