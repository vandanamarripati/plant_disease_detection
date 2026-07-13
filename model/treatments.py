"""
Small rule-based knowledge base of remedies/advice per disease.
Used to enrich model predictions with actionable guidance.
"""

TREATMENTS = {
    "Apple Scab": {
        "remedy": "Remove and destroy fallen leaves in autumn to reduce fungal spores. "
                   "Apply a fungicide (e.g. captan or myclobutanil) starting at bud break.",
        "prevention": "Choose scab-resistant apple varieties and prune for good air circulation.",
    },
    "Apple Black Rot": {
        "remedy": "Prune out dead or cankered wood. Apply fungicide sprays during the growing season.",
        "prevention": "Sanitize pruning tools and remove mummified fruit from the tree and ground.",
    },
    "Apple Cedar Rust": {
        "remedy": "Apply fungicide in spring when orange spore horns appear on nearby cedar trees.",
        "prevention": "Avoid planting apple trees within a few hundred meters of cedar/juniper hosts.",
    },
    "Cherry Powdery Mildew": {
        "remedy": "Apply sulfur-based or potassium bicarbonate fungicides at first sign of white powder.",
        "prevention": "Improve air circulation through pruning and avoid excess nitrogen fertilizer.",
    },
    "Corn Gray Leaf Spot": {
        "remedy": "Apply a foliar fungicide if disease appears before tasseling.",
        "prevention": "Rotate crops and till residue to reduce fungal carryover.",
    },
    "Corn Common Rust": {
        "remedy": "Fungicide application is rarely needed but can help in severe outbreaks on susceptible hybrids.",
        "prevention": "Plant rust-resistant hybrids.",
    },
    "Corn Northern Leaf Blight": {
        "remedy": "Apply fungicide at first sign of lesions, especially in humid weather.",
        "prevention": "Use resistant hybrids and rotate with non-host crops.",
    },
    "Grape Black Rot": {
        "remedy": "Remove mummified berries and apply fungicide from early shoot growth through veraison.",
        "prevention": "Prune for canopy airflow and clean up fallen debris each season.",
    },
    "Grape Esca (Black Measles)": {
        "remedy": "No effective chemical cure; remove and destroy severely infected vines/wood.",
        "prevention": "Avoid pruning wounds during wet weather and protect cuts with wound sealant.",
    },
    "Grape Leaf Blight": {
        "remedy": "Apply copper-based fungicide sprays and remove infected leaves.",
        "prevention": "Ensure good drainage and avoid overhead irrigation.",
    },
    "Orange Huanglongbing (Citrus Greening)": {
        "remedy": "No cure exists — remove and destroy infected trees to slow spread. Control psyllid insect vectors.",
        "prevention": "Use certified disease-free nursery stock and monitor for psyllids regularly.",
    },
    "Peach Bacterial Spot": {
        "remedy": "Apply copper-based bactericide sprays during dormancy and early season.",
        "prevention": "Plant resistant varieties and avoid excessive nitrogen fertilization.",
    },
    "Pepper Bell Bacterial Spot": {
        "remedy": "Apply copper-based bactericides; remove severely infected plants.",
        "prevention": "Use disease-free seed and avoid overhead watering.",
    },
    "Potato Early Blight": {
        "remedy": "Apply fungicide (chlorothalonil or mancozeb) at first symptoms and rotate crops.",
        "prevention": "Ensure adequate plant nutrition and avoid water stress.",
    },
    "Potato Late Blight": {
        "remedy": "Apply fungicide immediately (e.g. chlorothalonil) — this disease spreads fast and can destroy a crop.",
        "prevention": "Plant certified disease-free seed potatoes and destroy volunteer plants.",
    },
    "Squash Powdery Mildew": {
        "remedy": "Apply sulfur, neem oil, or potassium bicarbonate sprays at first sign of powder.",
        "prevention": "Space plants for airflow and water at the soil line, not on leaves.",
    },
    "Strawberry Leaf Scorch": {
        "remedy": "Remove infected leaves after harvest and apply fungicide if severe.",
        "prevention": "Avoid overhead watering and ensure good bed drainage.",
    },
    "Tomato Bacterial Spot": {
        "remedy": "Apply copper-based bactericide; remove and destroy infected foliage.",
        "prevention": "Use disease-free seed/transplants and avoid working in wet fields.",
    },
    "Tomato Early Blight": {
        "remedy": "Apply fungicide (chlorothalonil or copper) and remove lower infected leaves.",
        "prevention": "Mulch around plants and rotate crops each season.",
    },
    "Tomato Late Blight": {
        "remedy": "Apply fungicide immediately and remove infected plants — highly contagious and destructive.",
        "prevention": "Avoid overhead irrigation and ensure good airflow between plants.",
    },
    "Tomato Leaf Mold": {
        "remedy": "Improve ventilation and reduce humidity; apply fungicide if persistent.",
        "prevention": "Space plants well and avoid wetting foliage when watering.",
    },
    "Tomato Septoria Leaf Spot": {
        "remedy": "Remove infected lower leaves and apply fungicide at first symptoms.",
        "prevention": "Mulch soil to reduce spore splash and rotate crops annually.",
    },
    "Tomato Spider Mites": {
        "remedy": "Apply insecticidal soap or neem oil; increase humidity to discourage mites.",
        "prevention": "Regularly inspect leaf undersides and avoid drought stress.",
    },
    "Tomato Target Spot": {
        "remedy": "Apply fungicide and remove affected foliage promptly.",
        "prevention": "Ensure good air circulation and avoid leaf wetness.",
    },
    "Tomato Yellow Leaf Curl Virus": {
        "remedy": "No cure — remove and destroy infected plants to prevent whitefly-borne spread.",
        "prevention": "Control whitefly populations and use reflective mulches or row covers.",
    },
    "Tomato Mosaic Virus": {
        "remedy": "No cure — remove and destroy infected plants. Disinfect tools between plants.",
        "prevention": "Use resistant varieties and avoid handling plants after using tobacco products.",
    },
}

DEFAULT_HEALTHY_TIP = {
    "remedy": "No treatment needed — your plant looks healthy!",
    "prevention": "Keep monitoring regularly, maintain balanced watering and nutrition, "
                  "and inspect leaves weekly for early signs of stress or disease.",
}


def get_treatment(label: str, status: str) -> dict:
    if status == "healthy":
        return DEFAULT_HEALTHY_TIP
    return TREATMENTS.get(label, {
        "remedy": "Isolate the affected plant if possible and consult a local agricultural "
                  "extension office for a targeted treatment plan.",
        "prevention": "Practice crop rotation, remove infected debris, and avoid overhead watering.",
    })
