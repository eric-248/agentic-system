from sqlalchemy import Boolean, Column, Integer, String

from database import Base
from pydantic import BaseModel


class Todo(Base):
    __tablename__ = "todos"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    completed = Column(Boolean, default=False, nullable=False)


class TodoCreate(BaseModel):
    title: str
    description: str | None = None
    completed: bool = False


class TodoResponse(BaseModel):
    id: int
    title: str
    description: str | None
    completed: bool

    model_config = {"from_attributes": True}
