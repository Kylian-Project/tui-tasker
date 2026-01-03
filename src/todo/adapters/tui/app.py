from textual.app import App, ComposeResult
from textual.containers import Container, Grid
from textual.widgets import DataTable, Footer, Header, Static, OptionList, Input, TextArea, ProgressBar, RichLog, TabbedContent, TabPane
from textual.widgets.option_list import Option
from textual.screen import ModalScreen
from textual.binding import Binding

from typing import Any, Optional
from functools import partial
from datetime import date
from pathlib import Path
from whenever import Date as WheneverDate # type used to set date in DatePicker
from textual_timepiece.pickers import DatePicker

from todo.adapters.persistence.sqlite_repository import SQLiteTaskRepository, get_data_dir
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
                Option("Edit", id="edit"),
                None,
                Option("Mark as done", id="done"),
                Option("Mark as in progress", id="in_progress"),
                None,
                Option("Delete task", id="delete"),
                None,
                Option("Cancel", id="cancel"),
                id="action_list",
            )

    def on_mount(self) -> None:
        self.query_one("#action_list", OptionList).focus()

    def action_cancel(self) -> None:
        self.dismiss("cancel")

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        self.dismiss(event.option_id or "cancel")


class CreateTaskScreen(ModalScreen[dict[str, Any] | None]):
    BINDINGS = [
        ("escape", "cancel", "Cancel"),
        ("ctrl+s", "save", "Save"),
    ]

    def compose(self) -> ComposeResult:
        with Container(id="create_dialog"):
            yield Static("Create a task", id="create_title")
            yield Static("", id="create_error")

            with Grid(id="create_row_title_date"):
                yield Input(placeholder="Title (required)", max_length=30, id="create_title_input")
                yield DatePicker(id="create_due_input")

            yield TextArea(placeholder="Description (optional)", id="create_desc_input")

            yield OptionList(
                Option("Create (Ctrl+S)", id="create"),
                Option("Cancel (Esc)", id="cancel"),
                id="create_actions",
            )

    def on_mount(self) -> None:
        self.query_one("#create_title_input", Input).focus()

    def action_cancel(self) -> None:
        self.dismiss(None)

    def action_save(self) -> None:
        self.submit()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "create_title_input":
            self.query_one("#create_due_input", DatePicker).focus()

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        if event.option_id == "create":
            self.submit()
        else:
            self.dismiss(None)

    def set_error(self, message: str) -> None:
        self.query_one("#create_error", Static).update(message)
        self.app.bell()

    def submit(self) -> None:
        title = self.query_one("#create_title_input", Input).value.strip()
        desc = self.query_one("#create_desc_input", TextArea).text.strip() or None

        if not title or len(title) > 30:
            self.set_error("> Title is required or invalid.")
            self.query_one("#create_title_input", Input).focus()
            return

        picker = self.query_one("#create_due_input", DatePicker)
        due_before = picker.date

        if desc is not None and len(desc) > 115:
            self.set_error("> Description is too long (max 115 chars).")
            self.query_one("#create_desc_input", TextArea).focus()
            return

        due: date | None = None
        if due_before is not None:
            due = date(due_before.year, due_before.month, due_before.day)
        self.dismiss({"title": title, "due_date": due, "description": desc})

class EditTaskScreen(ModalScreen[dict[str, Any] | None]):
    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
        Binding("ctrl+s", "save", "Save", priority=True),
        Binding("ctrl+d", "clear_due", "Clear Date", priority=True),
    ]

    def __init__(self, task_id: int, title: str, description: str | None, due_date: date | None):
        super().__init__()
        self.task_id = task_id
        self.initial_title = title
        self.initial_description = description
        self.initial_due_date = due_date

    def compose(self) -> ComposeResult:
        with Container(id="edit_dialog"):
            yield Static(f"Edit task #{self.task_id}", id="edit_title")
            yield Static("", id="edit_error")

            with Grid(id="edit_row_title_date"):
                yield Input(placeholder="Title (required)", max_length=30, id="edit_title_input")
                yield DatePicker(id="edit_due_input")

            yield TextArea(placeholder="Description (optional)", id="edit_desc_input")

            yield OptionList(
                Option("Save (Ctrl+S)", id="save"),
                Option("Clear date (Ctrl+D)", id="clear_due"),
                Option("Cancel (Esc)", id="cancel"),
                id="edit_actions",
            )

    def on_mount(self) -> None:
        title_in = self.query_one("#edit_title_input", Input)
        desc_in = self.query_one("#edit_desc_input", TextArea)
        picker = self.query_one("#edit_due_input", DatePicker)

        title_in.value = self.initial_title
        desc_in.text = self.initial_description or ""

        if self.initial_due_date is not None:
            picker.date = WheneverDate(
                self.initial_due_date.year,
                self.initial_due_date.month,
                self.initial_due_date.day,
            )

        title_in.focus()

    def action_cancel(self) -> None:
        self.dismiss(None)

    def action_save(self) -> None:
        self.submit()

    def action_clear_due(self) -> None:
        self.query_one("#edit_due_input", DatePicker).action_clear()
        self.query_one("#edit_due_input", DatePicker).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "edit_title_input":
            self.query_one("#edit_due_input", DatePicker).focus()

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        if event.option_id == "clear_due":
            self.query_one("#edit_due_input", DatePicker).action_clear()
            self.query_one("#edit_due_input", DatePicker).focus()
            return

        if event.option_id == "save":
            self.submit()
        else:
            self.dismiss(None)

    def set_error(self, message: str) -> None:
        self.query_one("#edit_error", Static).update(message)
        self.app.bell()

    def submit(self) -> None:
        title = self.query_one("#edit_title_input", Input).value.strip()
        desc_text = self.query_one("#edit_desc_input", TextArea).text

        if not title or len(title) > 30:
            self.set_error("> Title is required or invalid.")
            self.query_one("#edit_title_input", Input).focus()
            return

        picker = self.query_one("#edit_due_input", DatePicker)
        due_before = picker.date
        due: date | None = None
        if due_before is not None:
            due = date(due_before.year, due_before.month, due_before.day)

        description = desc_text.strip()
        if len(description) > 115:
            self.set_error("> Description is too long (max 115 chars).")
            self.query_one("#edit_desc_input", TextArea).focus()
            return

        self.dismiss({"title": title, "due_date": due, "description": description})

class TaskTable(DataTable):
    BINDINGS = [
        Binding("enter", "open_actions", "Open action menu"),
    ]

    def action_open_actions(self) -> None:
        self.app.action_open_actions()

class OtherPanel(Container):
    def compose(self) -> ComposeResult:
        with TabbedContent(id="other_tabs"):
            with TabPane("Stats", id="tab_stats"):
                yield Static("Done", id="lbl_done")
                yield ProgressBar(total=1, show_eta=False, id="pb_done")

                yield Static("In Progress", id="lbl_in_progress")
                yield ProgressBar(total=1, show_eta=False, id="pb_in_progress")

                yield Static("Overdue", id="lbl_overdue")
                yield ProgressBar(total=1, show_eta=False, id="pb_overdue")

            with TabPane("Logs", id="tab_logs"):
                yield RichLog(id="activity_log", markup=True, highlight=True, auto_scroll=True)

class TaskApp(App):
    CSS_PATH = "app.css"

    BINDINGS = [
        ("a", "add_task", "Add Task"),
        ("r", "refresh", "Refresh Tasks"),
        ("q", "quit", "Exit"),
    ]

    def __init__(self):
        super().__init__()
        self.repo = SQLiteTaskRepository()
        self._notif_path = str(get_data_dir() / "notifications.txt")
        self._notif_offset = 0 # Ne pas lire les anciennes notifications
        self.notifier = Notif(self._notif_path)
        self._selected_task_id: Optional[int] = None

    def compose(self) -> ComposeResult:
        yield Header()

        with Grid(id="main_grid"):
            yield Section("Tasks list", TaskTable(id="task_table"), id="tasks_section")
            yield Section("Details", Static("", id="task_details"))
            yield Section("Infos", OtherPanel(), id="infos_section")

        yield Footer()

    def on_mount(self) -> None:
        self.title = "Tasker TUI"
        self.sub_title = "1.0.2"
        self.theme = "rose-pine-moon"

        table = self.query_one("#task_table", DataTable)
        table.add_column("ID", width=4)
        table.add_column("Title", width=30)
        table.add_column("Status", width=12)
        table.add_column("Due Date", width=12)
        table.cursor_type = "row"
        self.refresh_task_table()

        self.init_activity_log()
        self.set_interval(0.5, self.sec_notifications)

    def action_open_actions(self) -> None:
        table = self.query_one("#task_table", TaskTable)

        if table.row_count == 0:
            self.bell()
            return

        row_key = table.ordered_rows[table.cursor_row].key
        task_id = self.row_key_to_task_id(row_key)
        if task_id is None:
            self.bell()
            return

        task = get_task(self.repo, task_id)
        title = task.title if task else "Unknown"

        self.push_screen(
            TaskActionScreen(task_id, title),
            callback=partial(self.task_action, task_id),
        )
    
    def action_refresh(self) -> None:
        self.refresh_task_table(select_task_id=self._selected_task_id)

    def action_add_task(self) -> None:
        self.push_screen(CreateTaskScreen(), callback=self.create_task)

    def create_task(self, payload: dict[str, Any] | None) -> None:
        table = self.query_one("#task_table", DataTable)
        table.focus()

        if not payload:
            return

        title: str = payload["title"]
        due_date: date | None = payload.get("due_date")
        description: str | None = payload.get("description")

        try:
            created = create_task(
                repository=self.repo,
                notifier=self.notifier,
                title=title,
                due_date=due_date,
                description=description,
            )
        except TypeError:
            created = create_task(repository=self.repo, notifier=self.notifier, title=title, due_date=due_date)

        created_id = getattr(created, "id", None)
        self.refresh_task_table(select_task_id=created_id)

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
        
        self.update_stats(tasks)

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

        if action == "edit":
            task = get_task(self.repo, task_id)
            if not task:
                self.bell()
                table.focus()
                return

            self.push_screen(
                EditTaskScreen(task.id, task.title, task.description, task.due_date),
                callback=partial(self.edit_task, task_id, fallback_row),
            )
            return

        if action == "delete":
            delete_task(self.repo, self.notifier, task_id)
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

    def edit_task(self, task_id: int, fallback_row: int, payload: dict[str, Any] | None) -> None:
        table = self.query_one("#task_table", DataTable)
        table.focus()

        if not payload:
            return

        updated = update_task(
            repository=self.repo,
            notifier=self.notifier,
            task_id=task_id,
            title=payload.get("title"),
            description=payload.get("description"),
            due_date=payload.get("due_date"),
            status=None,
        )

        selected = getattr(updated, "id", None) or task_id
        self.refresh_task_table(select_task_id=selected, fallback_row=fallback_row)

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
            TaskStatus.OVERDUE: "bold #FC4949",
        }.get(task.status, "bold")

        details.update(
            "\n".join(
                [
                    f"[b]ID:[/b] {task.id}",
                    f"[b]Title:[/b] {task.title}",
                    f"[b]Status:[/b] [{status_style}]{task.status.value}[/]",
                    f"[b]Due date:[/b] {due}",
                    f"[b]Description:[/b] {desc}",
                ]
            )
        )

    # ---------------- Stats ----------------

    def update_stats(self, tasks) -> None:
        total = len(tasks)
        done = sum(1 for t in tasks if t.status == TaskStatus.DONE)
        in_progress = sum(1 for t in tasks if t.status == TaskStatus.IN_PROGRESS)
        today = date.today()
        overdue = sum(1 for t in tasks if t.status == TaskStatus.OVERDUE)

        self.query_one("#lbl_done", Static).update(f"Done {done}/{total}")
        self.query_one("#lbl_in_progress", Static).update(f"In Progress {in_progress}/{total}")
        self.query_one("#lbl_overdue", Static).update(f"Overdue {overdue}/{total}")

        pb_done = self.query_one("#pb_done", ProgressBar)
        pb_done.total = max(total, 1)
        pb_done.progress = done

        pb_in_progress = self.query_one("#pb_in_progress", ProgressBar)
        pb_in_progress.total = max(total, 1)
        pb_in_progress.progress = in_progress

        pb_overdue = self.query_one("#pb_overdue", ProgressBar)
        pb_overdue.total = max(total, 1)
        pb_overdue.progress = overdue


    def init_activity_log(self) -> None:
        log = self.query_one("#activity_log", RichLog)
        log.clear()

        try:
            with open(self._notif_path, "r", encoding="utf-8") as f:
                for line in f.read().splitlines():
                    if line.strip():
                        log.write(line)
                self._notif_offset = f.tell()
        except FileNotFoundError:
            self._notif_offset = 0


    def sec_notifications(self) -> None:
        log = self.query_one("#activity_log", RichLog)

        try:
            with open(self._notif_path, "r", encoding="utf-8") as f:
                f.seek(self._notif_offset)
                chunk = f.read()
                self._notif_offset = f.tell()
        except FileNotFoundError:
            return

        if not chunk:
            return

        for line in chunk.splitlines():
            if line.strip():
                log.write(line)

def run_tui() -> None:
    TaskApp().run()

if __name__ == "__main__":
    run_tui()
