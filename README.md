# Kestrel Home — Service-Request Routing

Routes each new Kestrel service request to one of 7 teams, explains why, and asks for a call-back when it is unsure.
Runs locally. No paid API, no API key, Rs 0 per request.

## Results (Apr–Jun 2026, 2,135 requests the model never trained on)

| | Correct team | Misroute cost per request |
|---|---|---|
| Current routing bot | 76.7% | Rs 173 |
| This model, all requests | 85.6% | Rs 107 |
| This model, confident requests only (85% of volume) | 97.0% | — |

"Correct team" means the team that actually closed the request (`final_team`), not the bot's original queue (`team_label`). See `logs/decisions.md` #1.

## Quick start

Requires Python 3.12.

**1. Install**
```bash
python -m venv env
# Windows:
env\Scripts\activate
# macOS / Linux:
source env/bin/activate
pip install -r requirements.txt
```

**2. Add the data pack**

Client data is not in this repository (Kestrel Ops Policy §10). Copy these files from the data pack into `data/`:
`train.csv`, `test_unlabelled.csv`, `resolution_log.csv`, `teams.csv`, `sample_submission.csv`

**3. Train the model** (about 1–2 minutes)
```bash
python src/04_features.py
```
Creates `outputs/model.joblib`.

**4. Start the service**
```bash
python -m uvicorn app.main:app --port 8000
```
Open http://127.0.0.1:8000 for the screen. Click an example, then "Route this request".

If step 3 was skipped, the service still starts and explains how to train the model instead of crashing.

## The endpoint

`POST /predict` takes one request as JSON:

```json
{
  "request_text": "my air fryer stopped heating after two weeks",
  "product_family": "Air Fryer",
  "warranty_status": "in_warranty",
  "channel": "chat"
}
```

It returns the team, confidence, whether to auto-route or call back, plain-English reasons, the next two likely teams, and what the chosen team handles.

Try it interactively at http://127.0.0.1:8000/docs, or from a terminal:

```bash
curl -X POST http://127.0.0.1:8000/predict -H "Content-Type: application/json" -d "{\"request_text\": \"i was charged twice for the same order\", \"product_family\": \"Water Purifier\", \"warranty_status\": \"in_warranty\", \"channel\": \"email\"}"
```

`GET /health` reports whether the model is trained.

## Rebuild predictions.csv
```bash
python src/05_predict.py
```
Writes `outputs/predictions.csv` (one row per `request_id`, one of the 7 team names).

## How it works
- **Model:** logistic regression on the message words, plus product, warranty status and channel.
- **Key finding:** when a message raises two issues, the **last** one decides the team (88% vs 48% for the first). The model reads the first and last issue separately.
- **Confidence threshold 0.5:** above it, auto-route (97% correct); below it, call the customer back first (a guess there is right only 21% of the time).
- **Same cleaning everywhere:** `src/prep.py` is shared by training and the service.

## Project layout
```
app/main.py            Service: /predict, /health, and the screen
app/static/index.html  The screen
src/prep.py            Shared cleaning (team renames, garbled text, message splitting)
src/01_audit.py        Data audit
src/02_models.py       First model comparison
src/03_errors.py       Error review file (local only)
src/04_features.py     Final model comparison and training
src/05_predict.py      Builds predictions.csv
logs/decisions.md      Every decision, with reason and evidence
logs/experiments.md    Every model tried: score, kept or dropped, why
logs/ai_log.md         How AI tools were used
outputs/predictions.csv
```

## Known limitations
- Training messages are templated. New wording (for example "package is broken") is often not recognised; the service then asks for a call-back rather than guessing.
- About 1.2% of training rows have a final team that contradicts their transfer history; these look like labelling errors.
- No hand-written routing rules and no LLM call: see `logs/decisions.md` #19 and #27.