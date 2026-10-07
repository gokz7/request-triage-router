# src/04_features.py
# Tests three error patterns found in manual review and saves the best model.
import sys
from datetime import datetime

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

import prep

ROOT = prep.ROOT
LOGS, OUT, WORK = ROOT / "logs", ROOT / "outputs", ROOT / "data" / "work"
for d in (LOGS, OUT, WORK):
    d.mkdir(parents=True, exist_ok=True)
COST = 742
SPLIT = "fit<2026-01, tune=Jan-Mar 2026 (selection), valid=Apr-Jun 2026 (report)"


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


tee = Tee(LOGS / "04_features.txt")
sys.stdout = tee


def log(name, feats, tune_acc, acc, f1, decision, reason):
    row = (f"| {datetime.now():%Y-%m-%d} | {name} | {feats} | {SPLIT} | tune acc / valid acc / valid macro-F1 | "
           f"{tune_acc:.3f} / {acc:.3f} / {f1:.3f} | {decision} | {reason} |\n")
    with open(LOGS / "experiments.md", "a", encoding="utf-8") as f:
        f.write(row)


def tfidf():
    return TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True)


def make_pipeline(kind, c):
    parts = [("txt", tfidf(), "text_clean")]
    cats = ["channel", "warranty_status"]
    cats += ["product_used", "combo_text"] if kind == "M5" else ["product_family", "combo"]
    if kind in ("M4", "M5"):
        parts += [("first", tfidf(), "first_seg"), ("last", tfidf(), "last_seg")]
        cats.append("n_seg_cat")
    parts.append(("cat", OneHotEncoder(handle_unknown="ignore"), cats))
    return Pipeline([("prep", ColumnTransformer(parts)),
                     ("clf", LogisticRegression(C=c, max_iter=3000, random_state=42))])


DESC = {
    "M2": "TF-IDF words + one-hot channel/product/warranty/combo (previous best)",
    "M4": "M2 + separate TF-IDF on first issue and last issue + issue count",
    "M5": "M4 but product taken from the text when it names one",
}

df = prep.load_train()
_, teams = prep.load_mapping()
fit = df[df["created_at_ist"] < "2026-01-01"]
tune = df[(df["created_at_ist"] >= "2026-01-01") & (df["created_at_ist"] < "2026-04-01")]
fit_tune = pd.concat([fit, tune])
valid = df[(df["created_at_ist"] >= "2026-04-01") & (df["created_at_ist"] < "2026-07-01")]
y_valid, bot = valid["final_team"], valid["team_label"]
test = prep.build_frame(pd.read_csv(prep.DATA_DIR / "test_unlabelled.csv"))

print("1. MESSAGE STRUCTURE")
print(f"Rows with 2+ issues: train {(df['n_seg'] >= 2).mean():.1%}, test {(test['n_seg'] >= 2).mean():.1%}")
multi = valid[valid["n_seg"] >= 2]
for col in ["first_seg", "last_seg"]:
    p = Pipeline([("v", ColumnTransformer([("t", tfidf(), col)])),
                  ("clf", LogisticRegression(C=2, max_iter=3000, random_state=42))]).fit(fit_tune, fit_tune["final_team"])
    print(f"Model trained on {col} only, accuracy on VALID 2+ issue rows ({len(multi)}): {accuracy_score(multi['final_team'], p.predict(multi)):.3f}")

print("\n2. PRODUCT COLUMN VS TEXT")
for name, d in [("train", df), ("valid", valid), ("test", test)]:
    named = (d["text_product"] != "").mean()
    print(f"{name}: text names a product {named:.1%}; product_family contradicts text {d['product_mismatch'].mean():.1%}")
print(f"Bot accuracy VALID: mismatch rows {accuracy_score(y_valid[valid['product_mismatch']], bot[valid['product_mismatch']]):.3f}, "
      f"other rows {accuracy_score(y_valid[~valid['product_mismatch']], bot[~valid['product_mismatch']]):.3f}")

print("\n3. MODELS (selected on TUNE, reported on VALID)")
results = []
for kind in ["M2", "M4", "M5"]:
    best_c, best_t = None, -1.0
    for c in [0.5, 2]:
        t = accuracy_score(tune["final_team"], make_pipeline(kind, c).fit(fit, fit["final_team"]).predict(tune))
        if t > best_t:
            best_c, best_t = c, t
    pipe = make_pipeline(kind, best_c).fit(fit_tune, fit_tune["final_team"])
    preds = pd.Series(pipe.predict(valid), index=valid.index)
    acc = accuracy_score(y_valid, preds)
    f1 = f1_score(y_valid, preds, average="macro", zero_division=0)
    print(f"{kind} C={best_c}: TUNE {best_t:.3f}, VALID {acc:.3f}, macro-F1 {f1:.3f}")
    results.append(dict(kind=kind, c=best_c, tune=best_t, acc=acc, f1=f1, preds=preds, pipe=pipe))

results.sort(key=lambda r: r["tune"], reverse=True)
best = results[0]
log(f"{best['kind']} C={best['c']}", DESC[best["kind"]], best["tune"], best["acc"], best["f1"], "Kept", "Highest TUNE accuracy")
for r in results[1:]:
    log(f"{r['kind']} C={r['c']}", DESC[r["kind"]], r["tune"], r["acc"], r["f1"], "Dropped",
        f"Lower TUNE accuracy than {best['kind']} ({r['tune']:.3f} vs {best['tune']:.3f})")

preds, pipe = best["preds"], best["pipe"]
print(f"\n4. BEST: {best['kind']} (C={best['c']}) VALID accuracy {best['acc']:.3f} vs bot {(bot == y_valid).mean():.3f}")
right = preds == y_valid
for label, m in [("2+ issues", valid["n_seg"] >= 2), ("1 issue", valid["n_seg"] < 2),
                 ("product mismatch", valid["product_mismatch"]), ("flag_contradiction", valid["flag_contradiction"])]:
    if m.any():
        print(f"{label}: rows {m.sum()}, model {right[m].mean():.3f}, bot {(bot == y_valid)[m].mean():.3f}")

print("\nCoverage (auto-route if top probability >= threshold):")
max_prob = pd.Series(pipe.predict_proba(valid).max(axis=1), index=valid.index)
for th in [0, 0.4, 0.5, 0.6, 0.7]:
    m = max_prob >= th
    print(f"Threshold {th:.1f}: auto-routed {m.mean():.1%}, accuracy {right[m].mean():.3f}, below-threshold accuracy "
          f"{right[~m].mean() if (~m).any() else float('nan'):.3f}")
print(f"Misroute cost per request: bot Rs {(bot != y_valid).mean() * COST:.0f}, model Rs {(~right).mean() * COST:.0f}")

out = valid[["request_id", "product_family", "text_product", "warranty_status", "channel", "n_seg", "team_label", "final_team"]].copy()
out["pred"], out["max_prob"] = preds, max_prob.round(3)
out.to_csv(WORK / "valid_predictions.csv", index=False)

final = make_pipeline(best["kind"], best["c"]).fit(df, df["final_team"])
joblib.dump({"pipeline": final, "team_names": teams, "C": best["c"], "model": best["kind"],
             "description": DESC[best["kind"]]}, OUT / "model.joblib")
print(f"\nSaved {best['kind']} refit on all train rows to outputs/model.joblib")

sys.stdout = tee.stdout
tee.file.close()