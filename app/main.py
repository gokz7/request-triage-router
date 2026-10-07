# app/main.py
# FastAPI service: one endpoint that routes a single request and explains why, plus one screen.
import sys
from pathlib import Path
from typing import Literal

import joblib
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import prep  # noqa: E402

MODEL_PATH = ROOT / "outputs" / "model.joblib"
THRESHOLD = 0.5
FILLER_WORDS = set(ENGLISH_STOP_WORDS) | {"pls", "please", "sir", "hi", "hello", "kindly", "asap",
                                          "team", "good", "morning", "thanks", "help", "need", "want"}

app = FastAPI(title="Kestrel service-request router")
_cache = {}


class ServiceRequest(BaseModel):
    request_text: str = Field(min_length=3, max_length=1000)
    product_family: Literal["Air Fryer", "Ceiling Fan", "Induction Cooktop", "Mixer Grinder",
                            "Robot Vacuum", "Room Heater", "Water Purifier"]
    warranty_status: Literal["in_warranty", "shield", "out_of_warranty"]
    channel: Literal["ivr", "chat", "whatsapp", "email"]


def get_model():
    if "bundle" not in _cache:
        if not MODEL_PATH.exists():
            raise HTTPException(
                status_code=503,
                detail="The routing model has not been trained on this machine yet. "
                       "Place the data pack in data/ and run: python src/04_features.py",
            )
        _cache["bundle"] = joblib.load(MODEL_PATH)
    return _cache["bundle"]


def get_team_handles():
    if "handles" not in _cache:
        try:
            mapping, _ = prep.load_mapping()
            teams = pd.read_csv(prep.DATA_DIR / "teams.csv")
            _cache["handles"] = {mapping[str(t).strip()]: h for t, h in zip(teams["team"], teams["handles"])}
        except Exception:
            _cache["handles"] = {}
    return _cache["handles"]


def is_filler(phrase):
    words = phrase.split()
    return len(phrase) < 3 or all(w in FILLER_WORDS or w.isdigit() for w in words)


def key_words(pipe, row, class_index, limit=4):
    """Words in this message that pushed the model most towards the chosen team."""
    pre, clf = pipe.named_steps["prep"], pipe.named_steps["clf"]
    x = pre.transform(row).tocsr()
    names = pre.get_feature_names_out()
    contrib = x.data * clf.coef_[class_index, x.indices]
    words = []
    for j in np.argsort(-contrib):
        if contrib[j] <= 0 or len(words) >= limit:
            break
        group, _, value = names[x.indices[j]].partition("__")
        if group not in ("txt", "first", "last") or is_filler(value):
            continue
        if any(value in w or w in value for w in words):
            continue
        words.append(value)
    return words


@app.get("/")
def screen():
    return FileResponse(ROOT / "app" / "static" / "index.html")


@app.get("/health")
def health():
    return {"status": "ok", "model_trained": MODEL_PATH.exists()}


@app.post("/predict")
def predict(req: ServiceRequest):
    bundle = get_model()
    pipe = bundle["pipeline"]
    row = prep.build_frame(pd.DataFrame([req.model_dump()]))
    probs = pipe.predict_proba(row)[0]
    order = np.argsort(-probs)
    best = int(order[0])
    team, confidence = str(pipe.classes_[best]), float(probs[best])
    auto = confidence >= THRESHOLD
    r = row.iloc[0]

    reasons = []
    words = key_words(pipe, row, best)
    if words:
        reasons.append(f"Words pointing to {team}: " + ", ".join(f'"{w}"' for w in words) + ".")
    if r["n_seg"] >= 2:
        reasons.append(f'The message raises {r["n_seg"]} issues; Kestrel routes by the last one: "{r["last_seg"]}".')
    if r["product_mismatch"]:
        reasons.append(f'Check: the product field says {r["product_family"]}, but the message mentions {r["text_product"]}.')
    if not auto and r["n_seg"] >= 2:
        reasons.append("The message raises more than one problem; confirm with the customer which one needs handling first.")
    elif not auto:
        reasons.append("The message does not clearly describe one problem, so a guess would often be wrong.")
    reasons.append(f'Details used: {req.product_family}, {req.warranty_status.replace("_", " ")}, {req.channel}.')

    return {
        "team": team,
        "confidence": round(confidence, 3),
        "auto_route": auto,
        "action": (f"Send to {team}." if auto else
                   "Low confidence: call the customer back and ask what the problem is before assigning a team."),
        "reasons": reasons,
        "alternatives": [{"team": str(pipe.classes_[i]), "confidence": round(float(probs[i]), 3)} for i in order[1:3]],
        "team_handles": get_team_handles().get(team, ""),
        "model": bundle.get("model", ""),
    }