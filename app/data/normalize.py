import pandas as pd

TICKET_TAG_COLUMNS = [f"tag_{i}" for i in range(1, 10)]


def normalize_ticket_df(df: pd.DataFrame) -> pd.DataFrame:
    working = df.copy()

    for column in [
        "subject",
        "body",
        "answer",
        "type",
        "queue",
        "priority",
        "language",
        "business_type",
        "source_dataset",
    ]:
        if column not in working.columns:
            working[column] = pd.NA

    available_tags = [col for col in TICKET_TAG_COLUMNS if col in working.columns]

    working["tags"] = working[available_tags].apply(
        lambda row: [str(v).strip() for v in row.tolist() if pd.notna(v) and str(v).strip()],
        axis=1,
    )

    working["ticket_text"] = (
        working["subject"].fillna("").astype(str).str.strip()
        + "\n\n"
        + working["body"].fillna("").astype(str).str.strip()
    ).str.strip()

    working["record_type"] = "ticket"

    ordered_columns = [
        "record_type",
        "source_dataset",
        "subject",
        "body",
        "ticket_text",
        "answer",
        "type",
        "queue",
        "priority",
        "language",
        "business_type",
        "tags",
    ]

    return working[ordered_columns]


def normalize_response_df(df: pd.DataFrame) -> pd.DataFrame:
    working = df.copy()

    for column in ["flags", "instruction", "category", "intent", "response", "source_dataset"]:
        if column not in working.columns:
            working[column] = pd.NA

    working["record_type"] = "response_example"
    working["language"] = "en"
    working["ticket_text"] = working["instruction"].fillna("").astype(str).str.strip()

    ordered_columns = [
        "record_type",
        "source_dataset",
        "flags",
        "instruction",
        "ticket_text",
        "category",
        "intent",
        "response",
        "language",
    ]

    return working[ordered_columns]


def build_dataset_summary(tickets_df: pd.DataFrame, responses_df: pd.DataFrame) -> dict:
    return {
        "ticket_rows": int(len(tickets_df)),
        "response_rows": int(len(responses_df)),
        "languages": sorted(tickets_df["language"].dropna().astype(str).unique().tolist()),
        "queues": int(tickets_df["queue"].nunique(dropna=True)),
        "priorities": sorted(tickets_df["priority"].dropna().astype(str).unique().tolist()),
        "types": sorted(tickets_df["type"].dropna().astype(str).unique().tolist()),
        "business_types": int(tickets_df["business_type"].dropna().astype(str).nunique()),
        "intents": int(responses_df["intent"].nunique(dropna=True)),
        "categories": int(responses_df["category"].nunique(dropna=True)),
    }