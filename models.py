from pydantic import BaseModel
import datetime
import typing as tp


class Comment(BaseModel):
    author_id: str
    text: str
    created_at: tp.Optional[datetime.datetime]


class Task(BaseModel):
    name: str
    description: str
    author_id: str
    comments: tp.List[Comment]
    assignee_id: str
    follower_ids: tp.List[str]
    slug: str
    start_time: datetime.datetime
    deadline: datetime.datetime
    status: str
    tags: tp.List[str]


class Status(BaseModel):
    name: str


class User(BaseModel):
    name: str
    photoUrl: str


class UserEntry(BaseModel):
    uid: str
    user: User


class Message(BaseModel):
    message: str