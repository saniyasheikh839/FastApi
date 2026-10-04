from typing import Annotated
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException, Path, Request
from starlette import status
from starlette.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from ..models import Todos
from ..database import SessionLocal
from .auth import get_current_user

templates = Jinja2Templates(directory='TodoApp/templates')

router = APIRouter(
    prefix="/todos",
    tags=["todos"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]


class TodoRequest(BaseModel):
    title: str = Field(min_length=3)
    description: str = Field(min_length=3, max_length=100)
    priority: int = Field(gt=0, lt=6)
    complete: bool = False


def redirect_to_login():
    redirect_response = RedirectResponse(url="/auth/login-page", status_code=status.HTTP_302_FOUND)
    redirect_response.delete_cookie(key="access_token")
    return redirect_response


### Pages ###

@router.get("/todo-page")
async def render_todo_page(request: Request, db: db_dependency):
    try:
        user = await get_current_user(request.cookies.get('access_token'))
        if user is None:
            return redirect_to_login()

        todos = db.query(Todos).filter(Todos.owner_id == user.get('id')).all()

        return templates.TemplateResponse(
            request, "todo.html", {"todos": todos, "user": user}
        )
    except Exception as e:
        print("todo-page error:", repr(e))
        return redirect_to_login()


@router.get('/add-todo-page')
async def render_add_todo_page(request: Request):
    try:
        user = await get_current_user(request.cookies.get('access_token'))

        if user is None:
            return redirect_to_login()

        return templates.TemplateResponse(
            request, "add-todo.html", {"user": user}
        )

    except Exception as e:
        print("add-todo-page error:", repr(e))
        return redirect_to_login()

@router.get("/edit-todo-page/{todo_id}")
async def render_edit_todo_page(request: Request, todo_id: int, db: db_dependency):
    try:
        user = await get_current_user(request.cookies.get('access_token'))

        if user is None:
            return redirect_to_login()

        todo = db.query(Todos).filter(Todos.id == todo_id)\
            .filter(Todos.owner_id == user.get('id')).first()

        if todo is None:
            return RedirectResponse(url="/todos/todo-page", status_code=status.HTTP_302_FOUND)

        return templates.TemplateResponse(
            request, "edit-todo.html", {"todo": todo, "user": user}
        )

    except Exception as e:
        print("edit-todo-page error:", repr(e))
        return redirect_to_login()

### Endpoints ###

def require_user(user):
    if user is None:
        raise HTTPException(status_code=401, detail='Authentication Failed')
    return user


def get_user_todo(db: Session, todo_id: int, user_id: int) -> Todos:
    todo_model = db.query(Todos).filter(Todos.id == todo_id)\
        .filter(Todos.owner_id == user_id).first()
    if todo_model is None:
        raise HTTPException(status_code=404, detail='Todo not found.')
    return todo_model


@router.get("/", status_code=status.HTTP_200_OK)
def read_all(user: user_dependency, db: db_dependency):
    user = require_user(user)
    return db.query(Todos).filter(Todos.owner_id == user.get('id')).all()


@router.get("/todo/{todo_id}", status_code=status.HTTP_200_OK)
def read_todo(user: user_dependency, db: db_dependency, todo_id: int = Path(gt=0)):
    user = require_user(user)
    return get_user_todo(db, todo_id, user.get('id'))


@router.post("/todo", status_code=status.HTTP_201_CREATED)
def create_todo(user: user_dependency, db: db_dependency, todo_request: TodoRequest):
    user = require_user(user)
    todo_model = Todos(**todo_request.model_dump(), owner_id=user.get('id'))

    db.add(todo_model)
    db.commit()
    db.refresh(todo_model)
    return todo_model


@router.put("/todo/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
def update_todo(user: user_dependency, db: db_dependency,
                todo_request: TodoRequest, todo_id: int = Path(gt=0)):
    user = require_user(user)
    todo_model = get_user_todo(db, todo_id, user.get('id'))

    todo_model.title = todo_request.title
    todo_model.description = todo_request.description
    todo_model.priority = todo_request.priority
    todo_model.complete = todo_request.complete

    db.commit()


@router.delete("/todo/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_todo(user: user_dependency, db: db_dependency, todo_id: int = Path(gt=0)):
    user = require_user(user)
    todo_model = get_user_todo(db, todo_id, user.get('id'))

    db.delete(todo_model)
    db.commit()