from pydantic import BaseModel, Field


class BenchmarkRunRequest(BaseModel):
    sample_size: int = Field(default=5, ge=1, le=50)
    random_seed: int = Field(default=42, ge=0, le=999999)
    include_rows: bool = True