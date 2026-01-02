from typing import Optional
from datetime import date

from todo.domain.task import Task, TaskStatus
from todo.application.ports import TaskRepository, Notifier


# =========================
# Création d'une tache
# =========================

def create_task(
    repository: TaskRepository,
    notifier: Notifier,
    title: str,
    description: Optional[str] = None,
    due_date: Optional[date] = None,
) -> Task:
    if not title or len(title) > 30:
        raise ValueError("Title is required and must be 1-30 characters long.")
    if description is not None and len(description) > 115:
        raise ValueError("Description must not exceed 115 characters.")
    task = Task(
        id=0, # Def par la BDD en auto increment
        title=title,
        description=description,
        due_date=due_date,
    )
    repository.add(task)
    notifier.notify(f"Tâche créée : {task.title} (id={task.id})")
    return task


# =========================
# Suppression d'une tache
# =========================

def delete_task(repository: TaskRepository, notifier: Notifier, task_id: int) -> bool:
    task = repository.get(task_id)
    if task is None:
        return False

    repository.delete(task_id)
    notifier.notify(f"Tâche supprimée : {task.title} (id={task.id})")
    return True


# =========================
# Récuperation tache
# =========================

def get_task(repository: TaskRepository, task_id: int) -> Optional[Task]:
    task = repository.get(task_id)
    if task is not None:
        update_overdue_tasks(repository, [task])
    return repository.get(task_id)

def list_tasks(repository: TaskRepository) -> list[Task]:
    tasks = repository.list()
    update_overdue_tasks(repository, tasks)
    return tasks


# =========================
# Mise à jour des teches en retard
# =========================
def update_overdue_tasks(repository: TaskRepository, tasks: list[Task]) -> None:
    for task in tasks:
        if (task.is_overdue()):
            task.status = TaskStatus.OVERDUE
            repository.update(task)


# =========================
# Mise a jour d'une tache
# =========================
def update_task(
    repository: TaskRepository,
    notifier: Notifier,
    task_id: int,
    title: Optional[str] = None,
    description: Optional[str] = None,
    status: Optional[str] = None,
    due_date: Optional[date] = None,
) -> Optional[Task]:
    task = repository.get(task_id)
    if task is None:
        return None

    before = (task.title, task.description, task.status, task.due_date)

    if title is not None:
        if not title or len(title) > 30:
            raise ValueError("Title is required and must be 1-30 characters long.")
        task.title = title
    if description is not None:
        if len(description) > 115:
            raise ValueError("Description must not exceed 115 characters.")
        task.description = description
    if status is not None:
        task.status = TaskStatus(status)
        if task.status == TaskStatus.IN_PROGRESS:
            update_overdue_tasks(repository, [task])
    if due_date is not None:
        task.due_date = due_date
        if (task.status == TaskStatus.OVERDUE and due_date >= date.today()):
            task.status = TaskStatus.IN_PROGRESS
    else:
        task.due_date = None

    updated = repository.update(task)
    after = (task.title, task.description, task.status, task.due_date)
    if before != after:
        notifier.notify(f"Tâche modifiée : {task.title} (id={task.id})")
    return updated

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

    if new_status == TaskStatus.DONE:
        task.mark_done()
    elif new_status == TaskStatus.IN_PROGRESS:
        task.mark_in_progress()

    if task.is_overdue():
        task.mark_overdue()

    if old_status != task.status:
        notifier.notify(
            f"Tache {task.id} : statut changé de {old_status.value} à {task.status.value}"
        )

    repository.update(task)
    return task
