# src/prep.py
# Shared cleaning for training and the API, so both see identical inputs.
import re
from pathlib import Path

import ftfy
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
SUFFIX = re.compile(r"\s*\(from .*\)$")

GREETING = re.compile(
    r"^(?:(?:hello team|hello|hi|hey|namaste|sir|madam|dear team|"
    r"good (?:morning|afternoon|evening)|pls help|please help)\b[\s\-,:!.]*)+"
)
FILLER = re.compile(
    r"(?:[\s,.\-]*(?:very disappointed|thank you|thanks|asap|kindly resolve|"
    r"pls call back|please call back|urgent))+$"
)
IDS = re.compile(r"\b(?:order|reg no|ref no|ref)\s*[a-z]{0,3}\d{4,}\b|\b[a-z]{2}\d{5,}\b")
PRODUCTS = [
    (re.compile(r"\bair fryers?\b|\bfryers?\b"), "Air Fryer"),
    (re.compile(r"\bmixers?\b|\bgrinders?\b"), "Mixer Grinder"),
    (re.compile(r"\bpurifiers?\b"), "Water Purifier"),
    (re.compile(r"\bvacuums?\b"), "Robot Vacuum"),
    (re.compile(r"\bcooktops?\b|\binduction\b"), "Induction Cooktop"),
    (re.compile(r"\bheaters?\b"), "Room Heater"),
    (re.compile(r"\bfans?\b"), "Ceiling Fan"),
]


def load_mapping():
    df = pd.read_csv(DATA_DIR / "teams.csv")
    mapping = {}
    for _, row in df.iterrows():
        old_name = str(row["team"]).strip()
        new_raw = row["renamed_to"]
        if pd.notna(new_raw) and str(new_raw).strip():
            new_raw = str(new_raw).strip()
            clean_new = SUFFIX.sub("", new_raw).strip()
            mapping[old_name] = clean_new
            mapping[new_raw] = clean_new
            mapping[clean_new] = clean_new
        else:
            mapping[old_name] = old_name
    return mapping, sorted(set(mapping.values()))


def clean_text(s):
    if pd.isna(s):
        return ""
    s = ftfy.fix_text(str(s)).lower()
    return re.sub(r"\s+", " ", s).strip()


def split_request(text):
    """Strip greetings, sign-offs and IDs, then split into comma-separated issues."""
    s = IDS.sub(" ", text)
    s = GREETING.sub("", s.strip())
    s = FILLER.sub("", s)
    s = re.sub(r"\s+", " ", s).strip(" ,.-")
    segs = [x.strip(" .-") for x in s.split(",") if x.strip(" .-")]
    if not segs:
        segs = [s]
    return segs[0], segs[-1], len(segs)


def detect_product(text):
    for pattern, name in PRODUCTS:
        if pattern.search(text):
            return name
    return ""


def build_frame(df):
    df = df.copy()
    df["text_clean"] = df["request_text"].apply(clean_text)
    parts = pd.DataFrame(df["text_clean"].apply(split_request).tolist(),
                         index=df.index, columns=["first_seg", "last_seg", "n_seg"])
    df[["first_seg", "last_seg", "n_seg"]] = parts
    df["n_seg_cat"] = df["n_seg"].clip(upper=3).astype(str)
    df["text_product"] = [detect_product(last) or detect_product(full)
                          for last, full in zip(df["last_seg"], df["text_clean"])]
    df["product_mismatch"] = (df["text_product"] != "") & (df["text_product"] != df["product_family"])
    df["product_used"] = df["text_product"].where(df["text_product"] != "", df["product_family"])
    df["combo"] = df["product_family"].astype(str) + "|" + df["warranty_status"].astype(str)
    df["combo_text"] = df["product_used"].astype(str) + "|" + df["warranty_status"].astype(str)
    return df


def load_train():
    train = pd.read_csv(DATA_DIR / "train.csv")
    res = pd.read_csv(DATA_DIR / "resolution_log.csv")
    df = train.merge(res, on="request_id", how="left")

    mapping, _ = load_mapping()
    for col in ["team_label", "first_team", "final_team"]:
        unknown = set(df[col].dropna()) - set(mapping)
        if unknown:
            raise ValueError(f"Unknown team names in {col}: {unknown}")
        df[col] = df[col].map(mapping)

    df["created_at_ist"] = pd.to_datetime(df["created_at_ist"])

    # Decision 4: legacy Zoho resolution times are UTC; convert to IST.
    df["resolved_at_ist"] = pd.to_datetime(df["resolved_at"])
    zoho = df["source"] == "legacy_zoho"
    df.loc[zoho, "resolved_at_ist"] = df.loc[zoho, "resolved_at_ist"] + pd.Timedelta(minutes=330)

    # Decision 6: flag rows with no transfers but a different closing team.
    df["flag_contradiction"] = (df["transfers"] == 0) & (df["first_team"] != df["final_team"])

    return build_frame(df)