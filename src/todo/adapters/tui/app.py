from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, DataTable

from todo.adapters.persistence.sqlite_repository import SQLiteTaskRepository
from todo.application.use_cases import (
    create_task,
    delete_task,
    update_task,
    get_task,
    list_tasks,
    change_task_status,
)

class TaskApp(App):
    BINDINGS = [
        ("q", "quit", "Quitter"),
        ("a", "add_task", "Ajouter"),
        ("enter", "toggle_done", "Valider"),
        ("d", "mark_done", "Terminer"),
        ("x", "delete_task", "Supprimer"),
        ("r", "refresh", "Rafraichir"),
    ]

    def __init__(self):
        super().__init__()
        self.repo = SQLiteTaskRepository()


    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        yield DataTable(id="task_table")

    def on_mount(self) -> None:
        table = self.query_one("#task_table", DataTable)
        table.add_columns("ID", "Title", "Status", "Due Date")
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

def run_tui():
    TaskApp().run()
