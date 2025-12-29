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
        id=0, # Def par la BDD en auto increment
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
    task = repository.get(task_id)
    if task is None:
        return False

    repository.delete(task_id)
    return True


# =========================
# Récuperation d'une tache
# =========================

def get_task(repository: TaskRepository, task_id: int) -> Optional[Task]:
    return repository.get(task_id)
