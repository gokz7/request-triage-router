# src/01_audit.py
# Data audit for Kestrel service-request routing. Prints counts only, never request text.
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
LOGS = ROOT / "logs"
LOGS.mkdir(parents=True, exist_ok=True)


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


def pct(x):
    return f"{x:.1%}"


def pct_dict(s):
    return {str(k): pct(v) for k, v in s.items()}


tee = Tee(LOGS / "01_audit.txt")
sys.stdout = tee

train = pd.read_csv(DATA / "train.csv")
test = pd.read_csv(DATA / "test_unlabelled.csv")
res_log = pd.read_csv(DATA / "resolution_log.csv")
teams = pd.read_csv(DATA / "teams.csv")

# 1
print("1. FILE STATS")
for name, df in [("train", train), ("test", test), ("resolution_log", res_log), ("teams", teams)]:
    nulls = {k: int(v) for k, v in df.isna().sum().items() if v > 0}
    print(f"{name}: {len(df)} rows, {len(df.columns)} cols, nulls: {nulls or 'none'}")

# 2
print("\n2. TEAM MAPPING")
SUFFIX = re.compile(r"\s*\(from .*\)$")
mapping = {}
for _, r in teams.iterrows():
    old = str(r["team"]).strip()
    if pd.notna(r["renamed_to"]) and str(r["renamed_to"]).strip():
        raw_new = str(r["renamed_to"]).strip()
        new = SUFFIX.sub("", raw_new)
        mapping[old] = new
        mapping[raw_new] = new
        mapping[new] = new
    else:
        mapping[old] = old
canon = sorted(set(mapping.values()))
print(f"Renames (old -> current): { {k: v for k, v in mapping.items() if k != v} }")
print(f"Current teams ({len(canon)}): {canon}")
unmapped = set()
for col, df in [("team_label", train), ("first_team", res_log), ("final_team", res_log)]:
    unmapped |= set(df[col].dropna()) - set(mapping)
print(f"Raw team values not covered by mapping: {unmapped or 'none'}")
sub = pd.read_csv(DATA / "sample_submission.csv")
print(f"sample_submission team values: {sorted(sub['team'].dropna().unique())}")

# 3
print("\n3. RESOLUTION LOG COVERAGE")
tf = train.merge(res_log, on="request_id", how="left")
print(f"Train rows with log row: {tf['first_team'].notna().sum()} ({pct(tf['first_team'].notna().mean())})")
print(f"Train rows with blank final_team: {tf['final_team'].isna().sum()}")
tf["created_dt"] = pd.to_datetime(tf["created_at_ist"], errors="coerce")
print(f"Unparseable created_at_ist: {tf['created_dt'].isna().sum()}")
tf["month"] = tf["created_dt"].dt.to_period("M")
cov = tf.groupby("month")["final_team"].apply(lambda s: s.notna().mean())
print(f"Lowest monthly coverage: {pct(cov.min())}")
print(f"Duplicate request_ids in log: {res_log['request_id'].duplicated().sum()}")

for c in ["team_label", "first_team", "final_team"]:
    tf[c] = tf[c].map(mapping).fillna(tf[c])

# 4
print("\n4. FIRST_TEAM VS TEAM_LABEL (after mapping)")
m = tf["first_team"] == tf["team_label"]
print(f"Match: {pct(m.mean())}, mismatches: {(~m).sum()}")

# 5
print("\n5. BOT ACCURACY (team_label == final_team)")
vf = tf.dropna(subset=["final_team"]).copy()
vf["acc"] = vf["team_label"] == vf["final_team"]
print(f"Overall: {pct(vf['acc'].mean())} ({vf['acc'].sum()} of {len(vf)})")
for col in ["month", "source", "channel", "product_family", "warranty_status"]:
    print(f"By {col}: {pct_dict(vf.groupby(col)['acc'].mean())}")

# 6
print("\n6. CROSSTAB (rows: team_label, cols: final_team)")
print(pd.crosstab(vf["team_label"], vf["final_team"]).to_string())

# 7
print("\n7. TRANSFERS")
dist = vf["transfers"].map(lambda x: "3+" if x >= 3 else str(int(x))).value_counts().sort_index()
print(f"Distribution: {dist.to_dict()}, mean: {vf['transfers'].mean():.2f}, total: {int(vf['transfers'].sum())}")
c1 = ((vf["transfers"] == 0) & (vf["first_team"] != vf["final_team"])).sum()
c2 = ((vf["transfers"] > 0) & (vf["first_team"] == vf["final_team"])).sum()
print(f"transfers==0 but first!=final: {c1}; transfers>0 but first==final: {c2}")

# 8
print("\n8. DATES")
test["created_dt"] = pd.to_datetime(test["created_at_ist"], errors="coerce")
test["month"] = test["created_dt"].dt.to_period("M")
print(f"Train requests/month: { {str(k): int(v) for k, v in tf['month'].value_counts().sort_index().items()} }")
print(f"Test requests/month: { {str(k): int(v) for k, v in test['month'].value_counts().sort_index().items()} }")
print(f"Test date range: {test['created_dt'].min()} to {test['created_dt'].max()}")
print(f"Train/test overlapping days: {len(set(tf['created_dt'].dt.date) & set(test['created_dt'].dt.date))}")

# 9
print("\n9. TIMESTAMPS (share of rows resolved before created)")
ts = vf[["source", "created_dt", "resolved_at"]].copy()
ts["res_dt"] = pd.to_datetime(ts["resolved_at"], errors="coerce")
print(f"Raw: {pct_dict((ts['res_dt'] < ts['created_dt']).groupby(ts['source']).mean())}")
zoho = ts["source"] == "legacy_zoho"
ts.loc[zoho, "res_dt"] = ts.loc[zoho, "res_dt"] + pd.Timedelta(minutes=330)
print(f"After +330 min on legacy_zoho: {pct_dict((ts['res_dt'] < ts['created_dt']).groupby(ts['source']).mean())}")

# 10
print("\n10. MOJIBAKE (share of rows with garbled characters)")
MOJ = r"Ã|â€|Â|ï¿½"
print(f"Train by source: {pct_dict(train['request_text'].str.contains(MOJ, na=False).groupby(train['source']).mean())}")
print(f"Test: {pct(test['request_text'].str.contains(MOJ, na=False).mean())}")

# 11
print("\n11. DUPLICATES")
print(f"Duplicate request_id: train {train['request_id'].duplicated().sum()}, test {test['request_id'].duplicated().sum()}, across {len(set(train['request_id']) & set(test['request_id']))}")
print(f"Unique texts: train {train['request_text'].nunique()} of {len(train)} rows; test {test['request_text'].nunique()} of {len(test)} rows")
groups = vf.groupby("request_text")["final_team"].agg(["size", "nunique"])
rep = groups[groups["size"] >= 2]
print(f"Train texts appearing 2+ times: {len(rep)}; of these with more than one final_team: {pct((rep['nunique'] > 1).mean())}")
majority = vf.groupby("request_text")["final_team"].agg(lambda s: s.value_counts().index[0])
vf["majority_team"] = vf["request_text"].map(majority)
print(f"Train rows whose final_team differs from their text's majority team: {pct((vf['final_team'] != vf['majority_team']).mean())}")
seen = test["request_text"].isin(set(train["request_text"]))
print(f"Unique texts shared train/test: {len(set(train['request_text']) & set(test['request_text']))}")
print(f"Test ROWS whose exact text appears in train: {seen.sum()} ({pct(seen.mean())})")
consistent = set(groups[groups["nunique"] == 1].index)
if seen.sum():
    print(f"  of those, text always maps to one final_team in train: {pct(test.loc[seen, 'request_text'].isin(consistent).mean())}")

# 12
print("\n12. FEATURE DISTRIBUTIONS (train% vs test%)")
for col in ["channel", "product_family", "warranty_status"]:
    d = pd.DataFrame({
        "train": train[col].value_counts(normalize=True),
        "test": test[col].value_counts(normalize=True),
    }).fillna(0).map(pct)
    print(f"\n{col}:\n{d.to_string()}")
print("\nRequest text length by channel (train):")
print(train.assign(n=train["request_text"].str.len()).groupby("channel")["n"].agg(["count", "median", "min", "max"]).to_string())

sys.stdout = tee.stdout
tee.file.close()