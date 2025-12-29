from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Date,
)
from sqlalchemy.orm import declarative_base, sessionmaker

from todo.domain.task import Task
from todo.application.ports import TaskRepository


# =========================
# Config SQLAlchemy
# =========================

DATABASE_URL = "sqlite:///todo.db"

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)

Base = declarative_base()


# =========================
# Table model
# =========================

class TaskTable(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    status = Column(String, nullable=False)
    due_date = Column(Date, nullable=True)


# Crée si pas existant
Base.metadata.create_all(bind=engine)


# =========================
# Repository SQLite
# =========================

class SQLiteTaskRepository(TaskRepository):
    """
    Implémentation SQLite du port TaskRepository
    """

    def add(self, task: Task) -> None:
        with SessionLocal() as session:
            orm_task = TaskTable(
                title=task.title,
                description=task.description,
                status=task.status.value,
                due_date=task.due_date,
            )
            session.add(orm_task)
            session.commit()
            session.refresh(orm_task)

    def delete(self, task_id: int) -> None:
        with SessionLocal() as session:
            orm_task = session.get(TaskTable, task_id)
            if orm_task is None:
                return
            session.delete(orm_task)
            session.commit()
