from pydantic import BaseModel, ConfigDict


class CurrentUser(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tier: str
