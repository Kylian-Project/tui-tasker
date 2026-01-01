from datetime import date
from enum import Enum


# =========================
# Exceptions
# =========================

class InvalidTaskTitle(Exception):
    """Levée lorsque le titre de la tâche est invalide."""
    pass


class InvalidTaskStatus(Exception):
    """Levée lorsque le statut de la tâche est invalide."""
    pass


# =========================
# Statut de la tâche
# =========================

class TaskStatus(str, Enum):
    IN_PROGRESS = "in_progress"
    DONE = "done"
    OVERDUE = "overdue"


# =========================
# Entité Task
# =========================

class Task:
    def __init__(
        self,
        id: int,
        title: str,
        description: str | None = None,
        status: TaskStatus = TaskStatus.IN_PROGRESS,
        due_date: date | None = None,
    ):
        if not title or not title.strip():
            raise InvalidTaskTitle("Le titre de la tâche est obligatoire.")

        if status not in TaskStatus:
            raise InvalidTaskStatus(f"Statut invalide : {status}")

        self.id = id
        self.title = title
        self.description = description
        self.status = status
        self.due_date = due_date

    def mark_done(self) -> None:
        """Marque la tâche comme terminée."""
        self.status = TaskStatus.DONE

    def mark_in_progress(self) -> None:
        """Marque la tâche comme en cours."""
        self.status = TaskStatus.IN_PROGRESS
    
    def mark_overdue(self) -> None:
        """Marque la tâche comme en retard."""
        self.status = TaskStatus.OVERDUE

    def is_overdue(self) -> bool:
        """Retourne True si la tâche est en retard."""
        if self.due_date is None:
            return False

        if self.status != TaskStatus.IN_PROGRESS:
            return False

        return self.due_date < date.today()
