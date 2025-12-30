from textual.app import App, ComposeResult
from textual.containers import Container, Grid
from textual.widgets import DataTable, Footer, Header, Input, Static

from todo.adapters.persistence.sqlite_repository import SQLiteTaskRepository
from todo.application.use_cases import (
    create_task,
    delete_task,
    update_task,
    get_task,
    list_tasks,
    change_task_status,
)
from todo.domain.task import TaskStatus


class Section(Container):
    def __init__(self, title: str, *children, **kwargs):
        super().__init__(*children, **kwargs)
        self.border_title = title

class TaskApp(App):
    CSS_PATH = "app.css"

    BINDINGS = [
        ("q", "quit", "Exit"),
        ("a", "add_task", "Add Task"),
        ("enter", "toggle_done", "Validate"),
        ("d", "mark_done", "Complete"),
        ("x", "delete_task", "Delete"),
        ("r", "refresh", "Refresh Tasks"),
    ]

    def __init__(self):
        super().__init__()
        self.repo = SQLiteTaskRepository()

    def compose(self) -> ComposeResult:
        yield Header()

        with Grid(id="main_grid"):
            yield Section("Tasks list", DataTable(id="task_table"), id="tasks_section")
            yield Section("Details", Static("WIP"))
            yield Section("Actions", Static("WIP"))

        yield Footer()

    def on_mount(self) -> None:
        self.title = "Tasker TUI"
        self.sub_title = "0.1.0"

        table = self.query_one("#task_table", DataTable)
        table.add_columns("ID", "Title", "Status", "Due Date")
        table.cursor_type = "row"
        table.zebra_stripes = True
        self.refresh_task_table()

    def refresh_task_table(self) -> None:
        table = self.query_one("#task_table", DataTable)
        table.clear()

        tasks = list_tasks(self.repo)
        for task in tasks:
            table.add_row(
                str(task.id),
                task.title,
                task.status.value,
                task.due_date.isoformat() if task.due_date else "N/A",
            )

    def action_refresh(self) -> None:
        self.refresh_task_table()

def run_tui() -> None:
    TaskApp().run()
