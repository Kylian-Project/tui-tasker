from abc import ABC, abstractmethod

from todo.domain.task import Task


# =========================
# Port de persistance
# =========================

class TaskRepository(ABC):
    """Port des opérations de persistance des tâches."""

    @abstractmethod
    def add(self, task: Task) -> None:
        pass

    @abstractmethod
    def delete(self, task_id: int) -> None:
        pass
