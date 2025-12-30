from datetime import date
from typing import Optional, List

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from todo.domain.task import TaskStatus
from todo.application.use_cases import (
    create_task,
    delete_task,
    update_task,
    get_task,
    list_tasks,
    change_task_status,
)
from todo.adapters.persistence.sqlite_repository import SQLiteTaskRepository
from todo.adapters.notifications.notif import Notif

app = FastAPI(title="TUI-tasker API", version="1.0.0")
repository = SQLiteTaskRepository()
notifier = Notif("notifications.txt")


# =========================
# Vérif Pydantic
# =========================

class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1)
    description: Optional[str] = None
    due_date: Optional[date] = None

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    due_date: Optional[date] = None

class TaskOut(BaseModel):
    id: int
    title: str
    description: Optional[str]
    status: TaskStatus
    due_date: Optional[date]

def out(task) -> TaskOut:
    return TaskOut(
        id=task.id,
        title=task.title,
        description=task.description,
        status=task.status,
        due_date=task.due_date,
    )


# =========================
# Endpoints REST
# =========================

@app.post("/tasks", response_model=TaskOut, status_code=201)
def api_create_task(payload: TaskCreate):
    task = create_task(
        repository=repository,
        title=payload.title,
        description=payload.description,
        due_date=payload.due_date,
    )
    return out(task)


@app.get("/tasks/{id}", response_model=TaskOut)
def api_get_task(id: int):
    task = get_task(repository, id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return out(task)

@app.get("/tasks", response_model=List[TaskOut])
def api_list_tasks():
    tasks = list_tasks(repository)
    return [out(t) for t in tasks]

@app.patch("/tasks/{id}", response_model=TaskOut)
def api_update_task(id: int, payload: TaskUpdate):
    # Si le statut est fourni : on utilise change_task_status
    if payload.status is not None:
        task = change_task_status(
            repository=repository,
            notifier=notifier,
            task_id=id,
            new_status=payload.status,
        )
        if task is None:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # On update les autres champs si besoin
        updated = update_task(
            repository=repository,
            task_id=id,
            title=payload.title,
            description=payload.description,
            status=None,
            due_date=payload.due_date,
        )
        if updated is None:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return out(updated)
    else:
        # Sinon simple update
        updated = update_task(
            repository=repository,
            task_id=id,
            title=payload.title,
            description=payload.description,
            status=None,
            due_date=payload.due_date,
        )
        if updated is None:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return out(updated)


@app.delete("/tasks/{id}", status_code=204)
def api_delete_task(id: int):
    ok = delete_task(repository, id)
    if not ok:
        raise HTTPException(status_code=404, detail="Task not found")
    return None
