from datetime import datetime

from todo.application.ports import Notifier


class Notif(Notifier):
    def __init__(self, path: str):
        self.path = path

    def notify(self, message: str) -> None:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with open(self.path, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {message}\n")
