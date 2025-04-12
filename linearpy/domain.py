from typing import Optional

from pydantic import BaseModel, Field

class Team(BaseModel):
    id: str
    name: str

class Issue(BaseModel):
    id: str
    title: str
    team: Team
    description: str
    priority: int = Field(default=1)
    parent: Optional["Issue"] = None
