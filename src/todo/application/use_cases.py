from typing import Optional
from datetime import date

from todo.domain.task import Task
from todo.application.ports import TaskRepository


# =========================
# Création d'une tache
# =========================

def create_task(
    repository: TaskRepository,
    title: str,
    description: Optional[str] = None,
    due_date: Optional[date] = None,
) -> Task:
    task = Task(
        id=0,
        title=title,
        description=description,
        due_date=due_date,
    )
    repository.add(task)
    return task


# =========================
# Suppression d'une tache
# =========================

def delete_task(repository: TaskRepository, task_id: int) -> bool:
    repository.delete(task_id)
    return True
