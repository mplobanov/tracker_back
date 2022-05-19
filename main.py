from fastapi import FastAPI, status, Request, Response, Header, Depends
from fastapi.responses import JSONResponse
import firebase_admin
from firebase_admin import credentials, exceptions
from firebase_admin import firestore, auth, _auth_utils
from fastapi.middleware.cors import CORSMiddleware
from models import *

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

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    try:
        CHECK = False
        if CHECK and request.method in ['GET', 'POST'] and \
                not (request.url.path.startswith(app.docs_url) or request.url.path.startswith(app.openapi_url)):
            token = request.headers['authorization'].split()[1]
            auth.verify_id_token(token)
        response: Response = await call_next(request)
        return response
    except exceptions.FirebaseError as e:
        print(e)
        return Response(status_code=status.HTTP_401_UNAUTHORIZED, content="Auth Failure")

cred = credentials.Certificate("tracker-76600-firebase-adminsdk-lvk4v-9a08a9c604.json")
firebase_admin.initialize_app(cred)

db = firestore.client()


async def get_uid(authorization=Header(default='a b')):
    token = authorization.split()[1]
    decoded_token = auth.verify_id_token(token)
    return decoded_token['uid']


@app.get("/list", response_model=tp.List[Task])
async def all_tasks() -> tp.List[Task]:
    docs = db.collection('tasks').stream()
    return [doc.to_dict() for doc in docs]


@app.get("/task/{slug}", response_model=tp.List[Task])
async def get_task(slug: str) -> tp.List[Task]:
    docs = db.collection('tasks').where('slug', '==', slug).stream()
    return [doc.to_dict() for doc in docs]


@app.get('/user/{uid}', response_model=User, responses={
    404: {"model": Message}
})
async def get_user(uid: str):
    try:
        user = auth.get_user(uid)
        return User(name=user.display_name, photoUrl=user.photo_url)
    except auth.UserNotFoundError as e:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"message": "Not Found"})


def check_slug(slug: str) -> bool:
    docs = db.collection('tasks').where('slug', '==', slug).stream()
    docs = [doc for doc in docs]
    return len(docs) > 0


@app.get('/task/exists/{slug}', response_model=Message)
async def task_exists(slug: str):
    return Message(message="Slug is already taken" if check_slug(slug) else "Slug is free")


@app.post('/task/{slug}/update', response_model=Task, responses={
    400: {"model": Message}
})
async def update_task(slug: str, task: Task):
    docs = db.collection('tasks').where('slug', '==', slug).stream()
    docs = [doc for doc in docs]
    if len(docs) != 1:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={
            "message": f"Wanted to find one, found {len(docs)}"
        })
    doc = docs[0]
    old_task = Task(**db.collection('tasks').document(doc.id).get().to_dict())
    if old_task.slug != task.slug:
        if check_slug(task.slug):
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={
                "message": f"Slug already taken"
            })
    print(old_task)
    # TODO check for comments
    db.collection('tasks').document(doc.id).set(task.dict(), merge=True)
    return Task(**db.collection('tasks').document(doc.id).get().to_dict())


@app.post('/task/create', response_model=Task, responses={
    400: {"model": Message}
})
async def create_task(task: Task):
    docs = db.collection('tasks').where('slug', '==', task.slug).stream()
    docs = [doc for doc in docs]
    if docs:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={
            "message": f"Slug already taken"
        })
    _, doc_ref = db.collection('tasks').add(task.dict())
    return Task(**db.collection('tasks').document(doc_ref.id).get().to_dict())


@app.get('/status/list', response_model=tp.List[Status])
async def get_status_list():
    docs = db.collection('statuses').stream()
    return [doc.to_dict() for doc in docs]


@app.post('/status/create', response_model=Status)
async def get_status_list(status: Status):
    _, doc_ref = db.collection('statuses').add(status.dict())
    return Status(**db.collection('statuses').document(doc_ref.id).get().to_dict())