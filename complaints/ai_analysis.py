import os
from pathlib import Path
import numpy as np
from ultralytics import YOLO

# Base directory and model path
BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_PATH = BASE_DIR / "ml_models" / "best.pt"

if not MODEL_PATH.exists():
    raise FileNotFoundError(f"Model file not found at: {MODEL_PATH}")

# Load YOLO model once
model = YOLO(str(MODEL_PATH))

# Map your class indices -> human-readable labels
CLASS_NAMES = {
    0: "pothole",
    1: "surface crack",
    2: "damaged road",
}

def analyze_road_damage(image_path: str, conf_threshold: float = 0.4) -> dict:
    """
    Run YOLO on the image and return a detailed analysis dict.
    Updated Logic: Evaluates cumulative damage to prevent 'low severity' misclassifications.
    """

    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found at: {image_path}")

    # Run inference with the specified confidence threshold
    results = model(image_path, conf=conf_threshold)
    
    if not results or len(results[0].boxes) == 0:
        return {
            "primary_label": "no_damage",
            "primary_confidence": 0.0,
            "severity": "low",
            "area_pixels": 0.0,
            "all_labels": [],
            "summary": "No significant road damage detected.",
        }

    res = results[0]
    boxes = res.boxes
    
    # Extract data to numpy for processing
    confs = boxes.conf.cpu().numpy()
    class_ids = boxes.cls.cpu().numpy().astype(int)
    xyxy = boxes.xyxy.cpu().numpy()

    # 1. Gather all detected labels
    all_labels = [CLASS_NAMES.get(cid, f"class_{cid}") for cid in class_ids]
    
    # 2. Identify the most confident detection
    best_idx = int(confs.argmax())
    primary_label = CLASS_NAMES.get(class_ids[best_idx], "unknown")
    primary_conf = float(confs[best_idx])

    # 3. ADVANCED SEVERITY LOGIC
    # We calculate total area and count detections to capture widespread damage
    total_area_pixels = 0
    pothole_count = 0
    
    for i, box in enumerate(xyxy):
        x1, y1, x2, y2 = box
        area = float(max(0.0, (x2 - x1) * (y2 - y1)))
        total_area_pixels += area
        if CLASS_NAMES.get(class_ids[i]) == "pothole":
            pothole_count += 1

    # Heuristic: High severity if there are many potholes OR a very large single damaged area
    # Adjust these thresholds based on your typical image resolution
    if pothole_count >= 3 or total_area_pixels > 100000:
        severity = "high"
    elif pothole_count >= 1 or total_area_pixels > 40000:
        severity = "medium"
    else:
        severity = "low"

    summary = (
        f"Detected {len(all_labels)} total issues ({pothole_count} potholes). "
        f"Primary detection: {primary_label} ({primary_conf:.2f} conf). "
        f"Status: {severity.upper()} severity."
    )

    return {
        "primary_label": primary_label,
        "primary_confidence": primary_conf,
        "severity": severity,
        "area_pixels": total_area_pixels, # Return total area instead of just the best one
        "all_labels": all_labels,
        "summary": summary,
    }