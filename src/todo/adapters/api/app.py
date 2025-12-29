from datetime import date
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from todo.domain.task import TaskStatus
from todo.application.use_cases import (
    create_task,
    delete_task,
    update_task,
)
from todo.adapters.persistence.sqlite_repository import SQLiteTaskRepository

app = FastAPI(title="TUI-tasker API", version="1.0.0")
repository = SQLiteTaskRepository()


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
    task = repository.get(id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return out(task)


@app.patch("/tasks/{id}", response_model=TaskOut)
def api_update_task(id: int, payload: TaskUpdate):
    updated = update_task(
        repository=repository,
        task_id=id,
        title=payload.title,
        description=payload.description,
        status=payload.status,
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
