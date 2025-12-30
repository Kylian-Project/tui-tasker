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
            yield Section("Details", Static("", id="task_details"))
            yield Section("Actions", Static("WIP"))

        yield Footer()

    def on_mount(self) -> None:
        self.title = "Tasker TUI"
        self.sub_title = "0.1.0"
        self.theme = "rose-pine-moon"

        table = self.query_one("#task_table", DataTable)
        table.add_columns("ID", "Title", "Status", "Due Date")
        table.cursor_type = "row"
        self.refresh_task_table()
    
    def action_refresh(self) -> None:
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
                key=str(task.id),
            )

        if table.row_count:
            table.move_cursor(row=0, column=0, scroll=True)
            self.update_details(table.ordered_rows[0].key)
        else:
            self.query_one("#task_details", Static).update("No task selected.")

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        self.update_details(event.row_key)

    def update_details(self, row_key) -> None:
        details = self.query_one("#task_details", Static)

        key_value = getattr(row_key, "value", row_key)

        try:
            task_id = int(str(key_value))
        except ValueError:
            details.update("No task selected.")
            return

        task = get_task(self.repo, task_id)
        if not task:
            details.update("Task not found.")
            return

        desc = (task.description or "").strip() or "—"
        due = task.due_date.isoformat() if task.due_date else "—"

        status_style = {
            TaskStatus.DONE: "bold #1EFB9D",
            TaskStatus.IN_PROGRESS: "bold #A187F0",
        }.get(task.status, "bold")

        details.update(
            "\n".join(
                [
                    f"[b]ID:[/b] {task.id}",
                    f"[b]Title:[/b] {task.title}",
                    f"[b]Status:[/b] [{status_style}]{task.status.value}[/]",
                    f"[b]Due date:[/b] {due}",
                    "",
                    "[b]Description:[/b]",
                    f"{desc}",
                ]
            )
        )

def run_tui() -> None:
    TaskApp().run()

if __name__ == "__main__":
    run_tui()
