"""
train_price_model.py
======================
Trains a RandomForestRegressor to predict crop market price (INR per
quintal) from crop type, month, and a year-index trend feature.

Unlike the disease-detection CNN, this model is lightweight enough to
train in seconds on a laptop CPU — no GPU or big dataset needed.

USAGE
-----
    python model/train_price_model.py

This reads data/crop_prices_sample.csv (bundled sample data) and writes
model/price_model.pkl + model/price_crops.json (the list of crops the
model was trained on, used to validate/encode requests at inference time).

To use REAL market data instead of the bundled sample:
  1. Download historical mandi price data for your crops/region from
     Agmarknet (agmarknet.gov.in) or data.gov.in.
  2. Reformat it to match the same columns as data/crop_prices_sample.csv:
         crop, year, month, price_per_quintal_inr
  3. Replace data/crop_prices_sample.csv with your real data (or point
     --data_path at your new file).
  4. Re-run this script — the app will automatically pick up the newly
     trained model on next restart.
"""

import argparse
import json
import os

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_path", default=os.path.join(BASE_DIR, "..", "data", "crop_prices_sample.csv"))
    parser.add_argument("--out", default=os.path.join(BASE_DIR, "price_model.pkl"))
    args = parser.parse_args()

    df = pd.read_csv(args.data_path)
    df = df.dropna()

    crops = sorted(df["crop"].unique().tolist())
    crop_to_idx = {c: i for i, c in enumerate(crops)}
    df["crop_idx"] = df["crop"].map(crop_to_idx)

    # A simple running "time index" feature lets the model learn a
    # long-term price trend in addition to the month-to-month seasonal cycle.
    min_year = df["year"].min()
    df["time_idx"] = (df["year"] - min_year) * 12 + df["month"]

    features = ["crop_idx", "month", "time_idx"]
    X = df[features]
    y = df["price_per_quintal_inr"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = RandomForestRegressor(n_estimators=200, max_depth=8, random_state=42)
    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    mae = mean_absolute_error(y_test, preds)
    r2 = r2_score(y_test, preds)
    print(f"Validation MAE: Rs. {mae:.2f} per quintal")
    print(f"Validation R^2: {r2:.3f}")

    joblib.dump({
        "model": model,
        "crop_to_idx": crop_to_idx,
        "min_year": int(min_year),
    }, args.out)
    print(f"Saved trained model to {args.out}")

    with open(os.path.join(BASE_DIR, "price_crops.json"), "w") as f:
        json.dump(crops, f, indent=2)
    print(f"Saved crop list ({len(crops)} crops) to model/price_crops.json")


if __name__ == "__main__":
    main()