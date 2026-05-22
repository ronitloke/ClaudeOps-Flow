from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

from app.core.settings import get_settings


def _clean_unique_values(series: pd.Series) -> List[str]:
    values = []
    for value in series.dropna().tolist():
        text = str(value).strip()
        if text and text.lower() != "nan":
            values.append(text)
    return sorted(set(values))


@lru_cache
def get_label_catalog() -> Dict[str, Any]:
    settings = get_settings()
    processed_dir = Path(settings.processed_data_dir)

    tickets_path = processed_dir / "tickets_unified.csv"
    responses_path = processed_dir / "responses_unified.csv"

    if not tickets_path.exists():
        raise FileNotFoundError(
            f"{tickets_path} not found. Run: python -m scripts.prepare_data"
        )

    if not responses_path.exists():
        raise FileNotFoundError(
            f"{responses_path} not found. Run: python -m scripts.prepare_data"
        )

    tickets_df = pd.read_csv(tickets_path)
    responses_df = pd.read_csv(responses_path)

    return {
        "queues": _clean_unique_values(tickets_df["queue"]),
        "priorities": _clean_unique_values(tickets_df["priority"]),
        "types": _clean_unique_values(tickets_df["type"]),
        "languages": _clean_unique_values(tickets_df["language"]),
        "business_types": _clean_unique_values(tickets_df["business_type"]),
        "intents": _clean_unique_values(responses_df["intent"]),
        "categories": _clean_unique_values(responses_df["category"]),
    }