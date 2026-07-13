"""
fertilizer.py
==============
A rule-based fertilizer recommendation engine.

Two modes:
1. Manual soil-test mode — the farmer enters current N, P, K (kg/ha) and
   soil pH for a chosen crop. We compare against ideal ranges and recommend
   specific fertilizers to correct any deficiency/excess.
2. Disease-linked mode — when a disease is detected on the Detect page and
   no soil test data is available, we give a general crop-appropriate
   fertilizer suggestion aimed at strengthening plant recovery/immunity,
   plus a nudge to run a full soil test for precision.

This is an educational rule-based tool, not a substitute for a proper
soil test or a certified agronomist's recommendation.
"""

# Ideal nutrient ranges (kg/ha) and pH range per crop — approximate,
# commonly cited agronomic targets for healthy growth.
CROP_REQUIREMENTS = {
    "Apple":       {"N": (50, 70),  "P": (25, 40), "K": (50, 70),  "ph": (6.0, 6.8)},
    "Blueberry":   {"N": (40, 60),  "P": (20, 30), "K": (40, 60),  "ph": (4.5, 5.5)},
    "Cherry":      {"N": (50, 70),  "P": (25, 40), "K": (50, 70),  "ph": (6.0, 7.0)},
    "Corn":        {"N": (120, 150),"P": (50, 70), "K": (40, 60),  "ph": (5.8, 6.8)},
    "Grape":       {"N": (40, 60),  "P": (20, 35), "K": (60, 90),  "ph": (5.5, 6.5)},
    "Orange":      {"N": (100, 130),"P": (30, 50), "K": (60, 90),  "ph": (6.0, 7.0)},
    "Peach":       {"N": (60, 80),  "P": (30, 45), "K": (60, 80),  "ph": (6.0, 6.8)},
    "Bell Pepper":  {"N": (100, 130),"P": (50, 70), "K": (80, 110), "ph": (6.0, 6.8)},
    "Potato":      {"N": (100, 140),"P": (50, 80), "K": (100, 150),"ph": (5.0, 6.0)},
    "Raspberry":   {"N": (50, 70),  "P": (25, 35), "K": (50, 70),  "ph": (5.6, 6.2)},
    "Soybean":     {"N": (20, 30),  "P": (40, 60), "K": (60, 90),  "ph": (6.0, 6.8)},
    "Squash":      {"N": (80, 110), "P": (40, 60), "K": (60, 90),  "ph": (6.0, 6.8)},
    "Strawberry":  {"N": (60, 90),  "P": (30, 45), "K": (80, 110), "ph": (5.5, 6.5)},
    "Tomato":      {"N": (100, 140),"P": (50, 80), "K": (100, 150),"ph": (6.0, 6.8)},
    "default":     {"N": (80, 120), "P": (40, 60), "K": (60, 90),  "ph": (6.0, 6.8)},
}

# Common fertilizer sources per nutrient (name + short note)
FERTILIZER_SOURCES = {
    "N": [
        {"name": "Urea (46-0-0)", "note": "Fast-acting nitrogen boost; apply in split doses to avoid leaching."},
        {"name": "Ammonium Sulfate (21-0-0)", "note": "Good for nitrogen-deficient, alkaline soils; also adds sulfur."},
    ],
    "P": [
        {"name": "DAP (18-46-0)", "note": "Strong phosphorus source; best applied at planting/root development stage."},
        {"name": "Single Super Phosphate (SSP)", "note": "Slow-release phosphorus, also supplies calcium and sulfur."},
    ],
    "K": [
        {"name": "MOP — Muriate of Potash (0-0-60)", "note": "Most common potassium source; supports fruit quality and disease resistance."},
        {"name": "SOP — Sulfate of Potash (0-0-50)", "note": "Chloride-free potassium, preferred for chloride-sensitive crops."},
    ],
    "balanced": [
        {"name": "NPK 19-19-19 (water soluble)", "note": "General-purpose balanced feed, good for foliar or fertigation use."},
        {"name": "Well-rotted farmyard manure / compost", "note": "Improves overall soil health and nutrient-holding capacity over time."},
    ],
}


def _status_for(value, ideal_range):
    low, high = ideal_range
    if value < low:
        return "low"
    if value > high:
        return "high"
    return "optimal"


def recommend_fertilizer(crop: str, n: float, p: float, k: float, ph: float) -> dict:
    """Manual mode: compare soil-test values against ideal ranges for the crop."""
    req = CROP_REQUIREMENTS.get(crop, CROP_REQUIREMENTS["default"])

    n_status = _status_for(n, req["N"])
    p_status = _status_for(p, req["P"])
    k_status = _status_for(k, req["K"])
    ph_status = _status_for(ph, req["ph"])

    recommendations = []
    for nutrient, status in [("N", n_status), ("P", p_status), ("K", k_status)]:
        if status == "low":
            recommendations.append({
                "nutrient": nutrient,
                "issue": "deficient",
                "fertilizers": FERTILIZER_SOURCES[nutrient],
            })
        elif status == "high":
            recommendations.append({
                "nutrient": nutrient,
                "issue": "excess",
                "fertilizers": [],
                "note": f"{nutrient} is already above the ideal range — skip {nutrient}-based "
                        f"fertilizers this season and retest before adding more.",
            })

    ph_note = None
    if ph_status == "low":
        ph_note = "Soil is more acidic than ideal — consider adding agricultural lime to raise pH."
    elif ph_status == "high":
        ph_note = "Soil is more alkaline than ideal — consider adding elemental sulfur or an acidifying fertilizer to lower pH."

    all_optimal = n_status == p_status == k_status == "optimal"

    return {
        "crop": crop,
        "soil_values": {"N": n, "P": p, "K": k, "ph": ph},
        "ideal_range": req,
        "status": {"N": n_status, "P": p_status, "K": k_status, "ph": ph_status},
        "recommendations": recommendations,
        "ph_note": ph_note,
        "all_optimal": all_optimal,
        "summary": (
            "Soil nutrients are within the ideal range for this crop — maintain your "
            "current fertilization schedule."
            if all_optimal else
            "Soil test shows one or more nutrients out of the ideal range — see the "
            "recommended fertilizers below."
        ),
    }


def recommend_for_disease(plant: str, status: str, severity: str) -> dict:
    """
    Disease-linked mode: no soil test data available, so give a general,
    crop-appropriate fertilizer suggestion aimed at supporting recovery,
    plus a nudge toward a full soil test for precision.
    """
    if status == "healthy":
        return {
            "applicable": False,
            "summary": "Plant looks healthy — no corrective fertilizer needed right now. "
                       "Maintain your regular feeding schedule.",
        }

    req = CROP_REQUIREMENTS.get(plant, CROP_REQUIREMENTS["default"])

    # Stressed/diseased plants generally benefit from balanced feeding rather
    # than a heavy single-nutrient push, plus potassium (supports disease
    # resistance) when severity is high.
    suggested = list(FERTILIZER_SOURCES["balanced"])
    if severity == "high":
        suggested = FERTILIZER_SOURCES["K"][:1] + suggested

    return {
        "applicable": True,
        "plant": plant,
        "target_range": req,
        "suggested_fertilizers": suggested,
        "summary": (
            f"Since {plant} shows signs of disease, avoid heavy nitrogen application right now "
            f"(it can encourage soft, disease-prone growth). A balanced feed helps the plant "
            f"recover, and potassium specifically supports disease resistance. For a precise "
            f"plan, run a soil test and use the full Fertilizer Recommendation tool."
        ),
    }