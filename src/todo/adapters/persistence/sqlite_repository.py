from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Date,
)
from sqlalchemy.orm import declarative_base, sessionmaker
from pathlib import Path

from todo.domain.task import Task, TaskStatus
from todo.application.ports import TaskRepository


# =========================
# Config SQLAlchemy
# =========================

def get_data_dir() -> Path:
    """Get application data directory, create if not exists."""
    if Path.home().joinpath("AppData").exists():  # Windows
        data_dir = Path.home() / "AppData" / "Local" / "tui-tasker"
    else:  # Linux/Mac
        data_dir = Path.home() / ".local" / "share" / "tui-tasker"
    
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir

DB_PATH = get_data_dir() / "todo.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

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
    
    def get(self, task_id: int) -> Task | None:
        with SessionLocal() as session:
            orm_task = session.get(TaskTable, task_id)

            if orm_task is None:
                return None
            
            return Task(
                id=orm_task.id,
                title=orm_task.title,
                description=orm_task.description,
                status=TaskStatus(orm_task.status),
                due_date=orm_task.due_date,
            )

    def update(self, task: Task) -> Task | None:
        with SessionLocal() as session:
            orm_task = session.get(TaskTable, task.id)

            if orm_task is None:
                return None

            orm_task.title = task.title
            orm_task.description = task.description
            orm_task.status = task.status.value
            orm_task.due_date = task.due_date

            session.commit()
            session.refresh(orm_task)

            return Task(
                id=orm_task.id,
                title=orm_task.title,
                description=orm_task.description,
                status=TaskStatus(orm_task.status),
                due_date=orm_task.due_date,
            )
        
    def list(self) -> list[Task]:
        with SessionLocal() as session:
            orm_tasks = session.query(TaskTable).all()
            tasks = [
                Task(
                    id=orm_task.id,
                    title=orm_task.title,
                    description=orm_task.description,
                    status=TaskStatus(orm_task.status),
                    due_date=orm_task.due_date,
                )
                for orm_task in orm_tasks
            ]
            return tasks
