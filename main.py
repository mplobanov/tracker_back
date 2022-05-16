import datetime

from fastapi import FastAPI, status
from fastapi.responses import JSONResponse
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore, auth
import typing as tp
from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel

app = FastAPI(
    title="🔥Tracker API"
)

origins = [
    "http://localhost.tiangolo.com",
    "https://localhost.tiangolo.com",
    "http://localhost:3000",
    "http://localhost:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

cred = credentials.Certificate("tracker-76600-firebase-adminsdk-lvk4v-9a08a9c604.json")
firebase_admin.initialize_app(cred)

db = firestore.client()

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


class User(BaseModel):
    name: str
    photoUrl: str

class Message(BaseModel):
    message: str

@app.get("/list", response_model=tp.List[Task])
async def all_tasks() -> tp.List[Task]:
    docs = db.collection('tasks').stream()
    return [doc.to_dict() for doc in docs]


@app.get("/task/{slug}", response_model=tp.List[Task])
async def get_task(slug: str) -> tp.List[Task]:
    docs = db.collection('tasks').where('slug', '==', slug).stream()
    return [doc.to_dict() for doc in docs]



@app.get('/verify', response_model=str)
async def verify(token: str) -> str:
    decoded_token = auth.verify_id_token(token)
    print(decoded_token)
    return decoded_token['uid']


@app.get('/user/{uid}', response_model=User, responses={
    404: {"model": Message}
})
async def get_user(uid: str):
    try:
        user = auth.get_user(uid)
        return User(name=user.display_name, photoUrl=user.photo_url)
    except auth.UserNotFoundError as e:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"message": "Not Found"})


@app.post('/task/{slug}/update', response_model=Task)
async def update_task(slug: str, task: Task):
    docs = db.collection('tasks').where('slug', '==', slug).stream()
    docs = [doc for doc in docs]
    if len(docs) != 1:
        return f"Wanted to find one, found {len(docs)}"

    doc = docs[0]
    db.collection('tasks').document(doc.id).set(task.dict(), merge=True)
    return Task(**db.collection('tasks').document(doc.id).get().to_dict())

@app.post('/task/create', response_model=Task)
async def create_task(task: Task):
    docs = db.collection('tasks').where('slug', '==', task.slug).stream()
    docs = [doc for doc in docs]
    if docs:
        return "Slug is already taken"
    _, doc_ref = db.collection('tasks').add(task.dict())
    return Task(**db.collection('tasks').document(doc_ref.id).get().to_dict())
