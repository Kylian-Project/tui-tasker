from typing import Optional
from datetime import date

from todo.domain.task import Task, TaskStatus
from todo.application.ports import TaskRepository, Notifier


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
# Récuperation tache
# =========================

def get_task(repository: TaskRepository, task_id: int) -> Optional[Task]:
    return repository.get(task_id)

def list_tasks(repository: TaskRepository) -> list[Task]:
    return repository.list()


# =========================
# Mise a jour d'une tache
# =========================
def update_task(
    repository: TaskRepository,
    task_id: int,
    title: Optional[str] = None,
    description: Optional[str] = None,
    status: Optional[str] = None,
    due_date: Optional[date] = None,
) -> Optional[Task]:
    task = repository.get(task_id)
    if task is None:
        return None

    if title is not None:
        task.title = title
    if description is not None:
        task.description = description
    if status is not None:
        task.status = TaskStatus(status)
    if due_date is not None:
        task.due_date = due_date
    else:
        task.due_date = None

    return repository.update(task)

# =========================
# Changement de statut
# =========================

def change_task_status(
    repository: TaskRepository,
    notifier: Notifier,
    task_id: int,
    new_status: TaskStatus,
) -> Optional[Task]:
    task = repository.get(task_id)
    if task is None:
        return None

    old_status = task.status

    if (old_status != new_status):
        if new_status == TaskStatus.DONE:
            task.mark_done()
        elif new_status == TaskStatus.IN_PROGRESS:
            task.mark_in_progress()

        notifier.notify(
            f"Tache {task.id} : statut changé de {old_status.value} à {task.status.value}"
        )

        repository.update(task)

    return task
