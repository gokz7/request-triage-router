# src/02_models.py
# Compares routing approaches on a time-based split and saves the best model.
import sys
from datetime import datetime

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

import prep

ROOT = prep.ROOT
LOGS_DIR = ROOT / "logs"
OUTPUTS_DIR = ROOT / "outputs"
WORK_DIR = ROOT / "data" / "work"
for d in (LOGS_DIR, OUTPUTS_DIR, WORK_DIR):
    d.mkdir(parents=True, exist_ok=True)

COST_PER_MISROUTE = 742
SPLIT_DESC = "fit<2026-01, tune=Jan-Mar 2026, valid=Apr-Jun 2026"
CAT_COLS = ["channel", "product_family", "warranty_status", "combo"]


class Tee:
    def __init__(self, path):
        self.stdout = sys.stdout
        self.file = open(path, "w", encoding="utf-8")

    def write(self, data):
        self.stdout.write(data)
        self.file.write(data)

    def flush(self):
        self.stdout.flush()
        self.file.flush()


tee = Tee(LOGS_DIR / "02_models.txt")
sys.stdout = tee


def log_experiment(approach, features, acc, f1, decision, reason):
    date = datetime.now().strftime("%Y-%m-%d")
    row = (f"| {date} | {approach} | {features} | {SPLIT_DESC} | "
           f"accuracy / macro-F1 | {acc:.3f} / {f1:.3f} | {decision} | {reason} |\n")
    with open(LOGS_DIR / "experiments.md", "a", encoding="utf-8") as f:
        f.write(row)


def make_pipeline(with_chars, c):
    parts = [("txt_w", TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True), "text_clean")]
    if with_chars:
        parts.append(("txt_c", TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5),
                                                min_df=2, sublinear_tf=True), "text_clean"))
    parts.append(("cat", OneHotEncoder(handle_unknown="ignore"), CAT_COLS))
    return Pipeline([
        ("prep", ColumnTransformer(parts)),
        ("clf", LogisticRegression(C=c, max_iter=2000, random_state=42)),
    ])


# ---------- Data and splits ----------
print("--- DATA AND SPLITS ---")
df = prep.load_train()
_, teams = prep.load_mapping()

fit = df[df["created_at_ist"] < "2026-01-01"]
tune = df[(df["created_at_ist"] >= "2026-01-01") & (df["created_at_ist"] < "2026-04-01")]
fit_tune = pd.concat([fit, tune])
valid = df[(df["created_at_ist"] >= "2026-04-01") & (df["created_at_ist"] < "2026-07-01")]
y_valid = valid["final_team"]
bot_valid = valid["team_label"]
print(f"FIT rows: {len(fit)}, TUNE rows: {len(tune)}, VALID rows: {len(valid)}")

results = []  # (name, features, acc, f1, preds, pipeline, C)

# ---------- Baselines ----------
acc0 = accuracy_score(y_valid, bot_valid)
f10 = f1_score(y_valid, bot_valid, average="macro", zero_division=0)
print(f"\nM0 bot baseline   VALID accuracy: {acc0:.3f}, macro-F1: {f10:.3f}")
log_experiment("M0 bot baseline", "team_label (bot queue)", acc0, f10, "Baseline", "Number to beat")

m1 = DummyClassifier(strategy="most_frequent").fit(fit_tune, fit_tune["final_team"])
p1 = m1.predict(valid)
acc1 = accuracy_score(y_valid, p1)
f11 = f1_score(y_valid, p1, average="macro", zero_division=0)
print(f"M1 majority class VALID accuracy: {acc1:.3f}, macro-F1: {f11:.3f}")
log_experiment("M1 majority class", "none", acc1, f11, "Baseline", "Floor")

# ---------- Candidate models ----------
for name, with_chars, feats in [
    ("M2 logistic regression", False, "TF-IDF words 1-2 + one-hot channel/product/warranty/combo"),
    ("M3 logistic regression", True, "M2 + TF-IDF chars 3-5"),
]:
    print(f"\n--- {name}: tuning C on TUNE ---")
    best_c, best_tune = None, -1.0
    for c in [0.5, 2, 8]:
        pipe = make_pipeline(with_chars, c).fit(fit, fit["final_team"])
        t_acc = accuracy_score(tune["final_team"], pipe.predict(tune))
        print(f"C={c}: TUNE accuracy {t_acc:.3f}")
        if t_acc > best_tune:
            best_c, best_tune = c, t_acc
    pipe = make_pipeline(with_chars, best_c).fit(fit_tune, fit_tune["final_team"])
    preds = pipe.predict(valid)
    acc = accuracy_score(y_valid, preds)
    f1 = f1_score(y_valid, preds, average="macro", zero_division=0)
    print(f"{name} (C={best_c}) VALID accuracy: {acc:.3f}, macro-F1: {f1:.3f}")
    results.append((name, feats, acc, f1, preds, pipe, best_c))

# ---------- Log kept / dropped ----------
results.sort(key=lambda r: r[2], reverse=True)
best = results[0]
log_experiment(f"{best[0]} C={best[6]}", best[1], best[2], best[3], "Kept", "Highest VALID accuracy")
for r in results[1:]:
    log_experiment(f"{r[0]} C={r[6]}", r[1], r[2], r[3], "Dropped",
                   f"Lower VALID accuracy than {best[0]} ({r[2]:.3f} vs {best[2]:.3f})")

name, feats, acc, f1, preds, pipe, best_c = best
preds = pd.Series(preds, index=valid.index)
print(f"\n=== BEST: {name} (C={best_c}) ===")

print("\nPer-team report (VALID):")
print(classification_report(y_valid, preds, labels=teams, zero_division=0, digits=3))

print("Confusion matrix (rows true, cols predicted):")
cm = confusion_matrix(y_valid, preds, labels=teams)
print(pd.DataFrame(cm, index=teams, columns=teams).to_string())

print("\nAccuracy by product family (model vs bot):")
for pf in sorted(valid["product_family"].unique()):
    m = valid["product_family"] == pf
    print(f"{pf}: model {accuracy_score(y_valid[m], preds[m]):.3f}, bot {accuracy_score(y_valid[m], bot_valid[m]):.3f}, rows {m.sum()}")

bot_right = bot_valid == y_valid
mod_right = preds == y_valid
print(f"\nVersus bot on VALID ({len(valid)} rows):")
print(f"Both right: {(bot_right & mod_right).sum()}")
print(f"Both wrong: {(~bot_right & ~mod_right).sum()}")
print(f"Bot right, model wrong: {(bot_right & ~mod_right).sum()}")
print(f"Model right, bot wrong: {(~bot_right & mod_right).sum()}")

print("\nCoverage table (auto-route only if top probability >= threshold):")
max_prob = pd.Series(pipe.predict_proba(valid).max(axis=1), index=valid.index)
for th in [0, 0.4, 0.5, 0.6, 0.7, 0.8]:
    m = max_prob >= th
    acc_th = accuracy_score(y_valid[m], preds[m]) if m.any() else float("nan")
    print(f"Threshold {th:.1f}: auto-routed {m.mean():.1%}, accuracy on those {acc_th:.3f}")

print(f"\nAverage misroute cost per request on VALID (Rs {COST_PER_MISROUTE} per misroute):")
print(f"Bot: Rs {(~bot_right).mean() * COST_PER_MISROUTE:.0f}")
print(f"Model: Rs {(~mod_right).mean() * COST_PER_MISROUTE:.0f}")

# Saved to data/work (git-ignored) because it contains request IDs.
out = valid[["request_id", "product_family", "warranty_status", "channel", "team_label", "final_team"]].copy()
out["pred"] = preds
out["max_prob"] = max_prob.round(3)
out.to_csv(WORK_DIR / "valid_predictions.csv", index=False)
print("\nSaved VALID predictions to data/work/valid_predictions.csv")

final_pipe = make_pipeline("chars" in feats, best_c).fit(df, df["final_team"])
joblib.dump({"pipeline": final_pipe, "team_names": teams, "C": best_c, "model": name},
            OUTPUTS_DIR / "model.joblib")
print("Refit on all train rows; saved to outputs/model.joblib")

sys.stdout = tee.stdout
tee.file.close()