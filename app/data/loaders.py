from pathlib import Path

import pandas as pd

PRIMARY_DATASET = "dataset-tickets-multi-lang-4-20k.csv"
BUSINESS_DATASET = "dataset-tickets-multi-lang3-4k.csv"
RESPONSE_DATASET = "Bitext_Sample_Customer_Support_Training_Dataset_27K_responses-v11.csv"


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    return pd.read_csv(path)


def load_primary_dataset(raw_dir: Path) -> pd.DataFrame:
    df = _read_csv(raw_dir / PRIMARY_DATASET).copy()
    df["source_dataset"] = "primary_support_tickets"

    if "business_type" not in df.columns:
        df["business_type"] = pd.NA

    return df


def load_business_dataset(raw_dir: Path) -> pd.DataFrame:
    df = _read_csv(raw_dir / BUSINESS_DATASET).copy()
    df["source_dataset"] = "business_support_tickets"
    return df


def load_response_dataset(raw_dir: Path) -> pd.DataFrame:
    df = _read_csv(raw_dir / RESPONSE_DATASET).copy()
    df["source_dataset"] = "bitext_responses"
    return df