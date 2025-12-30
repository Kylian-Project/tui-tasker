from textual.app import App


class TaskApp(App):
    def __init__(self):
        super().__init__()

def run_tui():
    TaskApp().run()
