from abc import ABC, abstractmethod
from typing import List

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

    @abstractmethod
    def get(self, task_id: int) -> Task | None:
        pass

    @abstractmethod
    def update(self, task: Task) -> Task | None:
        pass

    @abstractmethod
    def list(self) -> List[Task]:
        pass
