# src/05_predict.py
# Writes outputs/predictions.csv in the sample_submission format.
import joblib
import pandas as pd

import prep

ROOT = prep.ROOT
OUT = ROOT / "outputs"
THRESHOLD = 0.5

bundle = joblib.load(OUT / "model.joblib")
pipe, teams = bundle["pipeline"], bundle["team_names"]

sample = pd.read_csv(prep.DATA_DIR / "sample_submission.csv")
test = prep.build_frame(pd.read_csv(prep.DATA_DIR / "test_unlabelled.csv"))

probs = pipe.predict_proba(test)
test["team"] = pipe.classes_[probs.argmax(axis=1)]
test["max_prob"] = probs.max(axis=1)

sub = sample[["request_id"]].merge(test[["request_id", "team"]], on="request_id", how="left")
assert len(sub) == len(sample), "Row count differs from sample_submission"
assert sub["team"].notna().all(), "Some request_ids have no prediction"
assert set(sub["team"]) <= set(teams), "Prediction outside the 7 team names"
sub.to_csv(OUT / "predictions.csv", index=False)

train = prep.load_train()
compare = pd.DataFrame({
    "test predicted": sub["team"].value_counts(normalize=True),
    "train final_team": train["final_team"].value_counts(normalize=True),
}).fillna(0).map(lambda x: f"{x:.1%}")
print(f"Model: {bundle['model']} (C={bundle['C']})")
print(f"Wrote {len(sub)} rows to outputs/predictions.csv; columns: {list(sub.columns)}")
print(f"Low confidence (< {THRESHOLD}): {(test['max_prob'] < THRESHOLD).mean():.1%} of test rows")
print("\nTeam share, test predictions vs train actuals:")
print(compare.to_string())