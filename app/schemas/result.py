import json

from pydantic import BaseModel, field_validator


class DocumentResultResponse(BaseModel):
    word_count: int
    line_count: int
    keywords: list[str]
    summary: str

    @field_validator("keywords", mode="before")
    @classmethod
    def parse_keywords(cls, v: object) -> list[str]:
        if isinstance(v, str):
            return json.loads(v)
        return v
