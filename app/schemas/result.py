import json

from pydantic import BaseModel, ConfigDict, field_validator


class DocumentResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

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
