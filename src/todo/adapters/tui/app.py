from textual.app import App, ComposeResult
from textual.containers import Container, Grid
from textual.widgets import DataTable, Footer, Header, Static, OptionList
from textual.widgets.option_list import Option
from textual.screen import ModalScreen

from typing import Optional
from functools import partial

from todo.adapters.persistence.sqlite_repository import SQLiteTaskRepository
from todo.adapters.notifications.notif import Notif
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


class TaskActionScreen(ModalScreen[str]):
    BINDINGS = [
        ("escape", "cancel", "Cancel"),
        ("q", "cancel", "Cancel"),
    ]

    def __init__(self, task_id: int, task_title: str):
        super().__init__()
        self.task_id = task_id
        self.task_title = task_title

    def compose(self) -> ComposeResult:
        with Container(id="action_dialog"):
            yield Static(f"Task : #{self.task_id} • {self.task_title}", id="action_title")
            yield OptionList(
                Option("Marquer comme terminée", id="done"),
                Option("Marquer comme en cours", id="in_progress"),
                None,
                Option("Supprimer la tâche", id="delete"),
                None,
                Option("Annuler", id="cancel"),
                id="action_list",
            )

    def on_mount(self) -> None:
        self.query_one("#action_list", OptionList).focus()

    def action_cancel(self) -> None:
        self.dismiss("cancel")

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        self.dismiss(event.option_id or "cancel")


class TaskApp(App):
    CSS_PATH = "app.css"

    BINDINGS = [
        ("q", "quit", "Exit"),
        ("r", "refresh", "Refresh Tasks"),
    ]

    def __init__(self):
        super().__init__()
        self.repo = SQLiteTaskRepository()
        self.notifier = Notif("notifications.txt")
        self._selected_task_id: Optional[int] = None

    def compose(self) -> ComposeResult:
        yield Header()

        with Grid(id="main_grid"):
            yield Section("Tasks list", DataTable(id="task_table"), id="tasks_section")
            yield Section("Details", Static("", id="task_details"))
            yield Section("Calendar", Static("WIP"))

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
        self.refresh_task_table(select_task_id=self._selected_task_id)

    # ---------------- Table ----------------

    def refresh_task_table(self, select_task_id: Optional[int] = None, fallback_row: Optional[int] = None) -> None:
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

        if table.row_count == 0:
            self._selected_task_id = None
            self.query_one("#task_details", Static).update("No task selected.")
            return

        target_row = 0

        if select_task_id is not None:
            try:
                target_row = table.get_row_index(str(select_task_id))
            except Exception:
                target_row = 0
        elif fallback_row is not None:
            target_row = max(0, min(fallback_row, table.row_count - 1))

        table.move_cursor(row=target_row, column=0, scroll=True)
        row_key = table.ordered_rows[target_row].key
        self._selected_task_id = self.row_key_to_task_id(row_key)
        self.update_details(row_key)

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        self._selected_task_id = self.row_key_to_task_id(event.row_key)
        self.update_details(event.row_key)

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        task_id = self.row_key_to_task_id(event.row_key)
        if task_id is None:
            self.bell()
            return

        task = get_task(self.repo, task_id)
        title = task.title if task else "Unknown"

        self.push_screen(
            TaskActionScreen(task_id, title),
            callback=partial(self.task_action, task_id),
        )

    def task_action(self, task_id: int, action: Optional[str]) -> None:
        table = self.query_one("#task_table", DataTable)
        fallback_row = table.cursor_row

        if action in (None, "cancel"):
            table.focus()
            return

        if action == "delete":
            delete_task(self.repo, task_id)
            self.refresh_task_table(select_task_id=None, fallback_row=fallback_row)
            table.focus()
            return

        if action == "done":
            change_task_status(
                repository=self.repo,
                notifier=self.notifier,
                task_id=task_id,
                new_status=TaskStatus.DONE,
            )
        elif action == "in_progress":
            change_task_status(
                repository=self.repo,
                notifier=self.notifier,
                task_id=task_id,
                new_status=TaskStatus.IN_PROGRESS,
            )

        self.refresh_task_table(select_task_id=task_id, fallback_row=fallback_row)
        table.focus()

    def row_key_to_task_id(self, row_key) -> int | None:
        key_value = getattr(row_key, "value", row_key)
        try:
            return int(str(key_value))
        except ValueError:
            return None


    # ---------------- Details ----------------

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
