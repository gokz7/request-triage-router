# src/03_errors.py
# Summarises validation errors and writes a local review file (git-ignored) for manual reading.
import sys

import pandas as pd

import prep

ROOT = prep.ROOT
WORK = ROOT / "data" / "work"
LOGS = ROOT / "logs"


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


tee = Tee(LOGS / "03_errors.txt")
sys.stdout = tee

v = pd.read_csv(WORK / "valid_predictions.csv")
train = pd.read_csv(prep.DATA_DIR / "train.csv")[["request_id", "request_text"]]
v = v.merge(train, on="request_id", how="left")
v["correct"] = v["pred"] == v["final_team"]

print("1. ACCURACY BY CONFIDENCE BAND")
v["band"] = pd.cut(v["max_prob"], [0, 0.4, 0.6, 0.8, 1.0001], right=False,
                   labels=["<0.4", "0.4-0.6", "0.6-0.8", ">=0.8"])
print(v.groupby("band", observed=True)["correct"].agg(rows="size", accuracy="mean").round(3).to_string())

print("\n2. TOP 10 ERROR TYPES (true -> predicted)")
err = v[~v["correct"]]
print((err["final_team"] + " -> " + err["pred"]).value_counts().head(10).to_string())

low = v[v["max_prob"] < 0.4]
print(f"\n3. LOW-CONFIDENCE ROWS (<0.4): {len(low)} ({len(low) / len(v):.1%})")
print("By product:", low["product_family"].value_counts(normalize=True).round(3).to_dict())
print("By channel:", low["channel"].value_counts(normalize=True).round(3).to_dict())
print("Predicted team:", low["pred"].value_counts().to_dict())

print("\n4. IF SCORED AGAINST THE BOT LABEL INSTEAD")
print(f"Model matches team_label: {(v['pred'] == v['team_label']).mean():.3f}")

sample = pd.concat([
    err[err["max_prob"] >= 0.4].sample(n=min(30, (err["max_prob"] >= 0.4).sum()), random_state=42).assign(group="confident_error"),
    low.sample(n=min(20, len(low)), random_state=42).assign(group="low_confidence"),
])
cols = ["group", "request_id", "product_family", "warranty_status", "channel",
        "team_label", "final_team", "pred", "max_prob", "request_text"]
sample[cols].to_csv(WORK / "errors_review.csv", index=False, encoding="utf-8-sig")
print(f"\nWrote {len(sample)} rows to data/work/errors_review.csv for manual review")

sys.stdout = tee.stdout
tee.file.close()