"""
PlantDiseaseDetector
=====================
Wraps a trained MobileNetV2-based classifier (see train_model.py) and exposes
a single `.predict(image)` method that always returns a consistent response,
whether or not a trained model file is present.

If no trained `.h5` model is found on disk, the detector automatically falls
back to a lightweight color/texture heuristic ("demo mode") so the full
application is runnable end-to-end without first downloading a dataset and
training a model. Swap in real trained weights at any time — no other code
needs to change.
"""

import json
import os
import random

import numpy as np
from PIL import Image

from model.treatments import get_treatment

IMG_SIZE = (224, 224)


class PlantDiseaseDetector:
    def __init__(self, model_path: str, labels_path: str):
        self.model_path = model_path
        self.labels = self._load_labels(labels_path)
        self.model = None
        self.demo_mode = True

        if os.path.exists(model_path):
            try:
                # Imported lazily so the app can run even if tensorflow
                # isn't installed yet (demo mode needs only Pillow/numpy).
                import tensorflow as tf
                self.model = tf.keras.models.load_model(model_path)
                self.demo_mode = False
                print(f"[PlantDiseaseDetector] Loaded trained model from {model_path}")
            except Exception as exc:
                print(f"[PlantDiseaseDetector] Could not load model ({exc}); using demo mode.")
        else:
            print(f"[PlantDiseaseDetector] No trained model found at {model_path}. "
                  f"Running in DEMO MODE with a heuristic classifier. "
                  f"See model/train_model.py to train a real one.")

    @staticmethod
    def _load_labels(labels_path: str) -> dict:
        with open(labels_path, "r") as f:
            return json.load(f)

    # ------------------------------------------------------------------
    def predict(self, image: Image.Image) -> dict:
        if self.model is not None:
            probs = self._predict_with_model(image)
        else:
            probs = self._predict_heuristic(image)

        top_idx = int(np.argmax(probs))
        confidence = float(probs[top_idx])
        info = self.labels[str(top_idx)]

        # Build a top-3 breakdown for the UI
        top3_idx = np.argsort(probs)[::-1][:3]
        top3 = [
            {
                "label": self.labels[str(i)]["label"],
                "confidence": round(float(probs[i]) * 100, 1),
            }
            for i in top3_idx
        ]

        treatment = get_treatment(info["label"], info["status"])

        return {
            "label": info["label"],
            "plant": info["plant"],
            "status": info["status"],
            "severity": info["severity"],
            "confidence": round(confidence * 100, 1),
            "top3": top3,
            "remedy": treatment["remedy"],
            "prevention": treatment["prevention"],
        }

    # ------------------------------------------------------------------
    def _predict_with_model(self, image: Image.Image) -> np.ndarray:
        import tensorflow as tf
        img = image.resize(IMG_SIZE)
        arr = np.array(img).astype("float32") / 255.0
        arr = np.expand_dims(arr, axis=0)
        preds = self.model.predict(arr, verbose=0)[0]
        return preds

    def _predict_heuristic(self, image: Image.Image) -> np.ndarray:
        """
        Demo-mode fallback: derives a plausible-looking probability
        distribution from simple color statistics (fraction of brown/yellow
        vs. green pixels). This is NOT a real disease classifier — it exists
        purely so the app is fully interactive before you train and drop in
        real model weights.
        """
        img = image.resize((128, 128))
        arr = np.array(img).astype("float32") / 255.0
        r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]

        green_mask = (g > r) & (g > b)
        green_ratio = float(green_mask.mean())

        brown_yellow_mask = (r > 0.35) & (g > 0.25) & (b < 0.35) & (r >= g)
        spot_ratio = float(brown_yellow_mask.mean())

        num_classes = len(self.labels)
        rng = random.Random(int(arr.sum() * 1000) % (2**31))
        probs = np.array([rng.random() * 0.05 for _ in range(num_classes)])

        healthy_indices = [int(k) for k, v in self.labels.items() if v["status"] == "healthy"]
        diseased_indices = [int(k) for k, v in self.labels.items() if v["status"] == "diseased"]

        if green_ratio > 0.55 and spot_ratio < 0.12:
            # Looks like a clean, healthy green leaf
            winner = rng.choice(healthy_indices)
            probs[winner] += 0.55 + spot_ratio
        else:
            # Enough discoloration to suggest a disease pattern
            winner = rng.choice(diseased_indices)
            probs[winner] += 0.45 + min(spot_ratio, 0.4)

        probs = probs / probs.sum()
        return probs
