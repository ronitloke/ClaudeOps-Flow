import json
from pathlib import Path

import pandas as pd

from app.core.settings import get_settings
from app.data.loaders import (
    load_business_dataset,
    load_primary_dataset,
    load_response_dataset,
)
from app.data.normalize import (
    build_dataset_summary,
    normalize_response_df,
    normalize_ticket_df,
)


def main() -> None:
    settings = get_settings()
    raw_dir = Path(settings.raw_data_dir)
    processed_dir = Path(settings.processed_data_dir)

    processed_dir.mkdir(parents=True, exist_ok=True)

    primary_df = load_primary_dataset(raw_dir)
    business_df = load_business_dataset(raw_dir)
    responses_df = load_response_dataset(raw_dir)

    tickets_df = pd.concat(
        [
            normalize_ticket_df(primary_df),
            normalize_ticket_df(business_df),
        ],
        ignore_index=True,
    )

    responses_norm_df = normalize_response_df(responses_df)

    tickets_path = processed_dir / "tickets_unified.csv"
    responses_path = processed_dir / "responses_unified.csv"
    summary_path = processed_dir / "dataset_summary.json"

    tickets_df.to_csv(tickets_path, index=False)
    responses_norm_df.to_csv(responses_path, index=False)

    summary = build_dataset_summary(tickets_df, responses_norm_df)
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print("Saved:", tickets_path)
    print("Saved:", responses_path)
    print("Saved:", summary_path)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()