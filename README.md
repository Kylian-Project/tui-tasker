<link href='https://cdn.boxicons.com/3.0.6/fonts/basic/boxicons.min.css' rel='stylesheet'>

# TUI-Tasker

Task manager with TUI interface and REST API.

---

## <i class='bx  bx-git-branch'></i>  Features

### TUI
- Create, edit, delete tasks
- Mark as done or in progress
- Due dates with automatic overdue detection
- Visual statistics (progress bars)
- Real-time activity log
- Keyboard and mouse navigation

### REST API
- Full CRUD (`GET`, `POST`, `PATCH`, `DELETE`)
- Secured by API Key
- Auto documentation (Swagger)
- Data validation (Pydantic)

### Business logic
- Hexagonal architecture
- Validation: title max 30 chars, description max 115 chars
- 3 statuses: `IN_PROGRESS`, `DONE`, `OVERDUE`
- Automatic notifications (notifications.txt)
- SQLite database

---

## Images

- **Main screen**
![TUI main](assets/main.png)

- **Create task**
![TUI create](assets/create.png)

- **Edit task**
![TUI edit](assets/edit.png)

- **Actions menu**
![TUI actions](assets/actions.png)

---

## <i class='bx  bx-spanner'></i>  Installation

### User mode
```bash
poetry install
```

### Dev mode
```bash
poetry install --with dev
```

---

## <i class='bx  bx-scroll'></i>  Usage

### Launch TUI
```bash
poetry run python -m todo.adapters.tui.app
```

### Launch API
```bash
# Create a .env file at the root
echo "API_KEY=your-secret-key-here" > .env

# Start the server
poetry run uvicorn todo.adapters.api.api:app --reload

# Access Swagger documentation
# http://localhost:8000/docs
# (Don't forget to set the API key in the top right if you want to test endpoints on the doc)
```

### Tests
```bash
# All tests
poetry run pytest

# With details
poetry run pytest -v
```

### Test API

##### With Bruno (provided collection)
```bash
cd bruno-coll/TUI-tasker
# Open with Bruno Desktop (don't forget to configure the API Key in the collection Headers)
```

---

## <i class='bx  bx-link'></i>  Dependencies

### Production

| Package | Role |
|---------|------|
| **sqlalchemy** | ORM for SQLite |
| **fastapi** | REST API framework |
| **pydantic** | Data validation |
| **uvicorn** | Server to run FastAPI |
| **rich** | Terminal rendering (used by Textual) |
| **textual** | Modern TUI framework |
| **textual-timepiece** | DatePicker widget for Textual |
| **python-dotenv** | Environment variables management (.env) |

### Development

| Package | Role |
|---------|------|
| **textual-dev** | Textual DevTools (debug console, reload) |
| **pytest** | Unit testing framework |
| **pytest-cov** | Test code coverage |

---

## <i class='bx  bx-brush-sparkles'></i>  Design & Technical choices

### Why Textual?
- **Inspiration**: **Posting** application briefly seen in class and which uses textual.
- **Advantages**:
  - Modern framework based on Rich
  - CSS-like for styling
  - Widgets (DataTable, ProgressBar, TabbedContent)
  - Live reload in dev
  - Good documentation: [Textual Docs](https://textual.textualize.io/)

### Color palette
> Also inspired by the posting theme.

**Textual theme**: Rose Pine Moon

| Color | Hex | Usage |
|---------|-----|-------|
| **Background** | `#20212f` | Background |
| **Primary** | `#d563a8` | Headers, borders, titles |
| **Secondary** | `#9775DC` | Accents, highlights |
| **Violet** | `#892DE1` | Table headers, scrollbars |
| **Success** | `#1EFB9D` | Completed tasks |
| **Warning** | `#A187F0` | In progress tasks |
| **Error** | `#FC4949` | Overdue tasks |

---

## <i class='bx  bx-building'></i>  Architecture

### Hexagonal (Ports & Adapters)

```
src/todo/
├── domain/              # Business entities (Task)
├── application/         # Use cases + Ports (interfaces)
└── adapters/            # Implementations
    ├── api/             # REST Adapter (FastAPI)
    ├── tui/             # Terminal Adapter (Textual)
    ├── persistence/     # SQLite Adapter
    └── notifications/   # Notifications file Adapter
```

### Project structure

```
tui-tasker/
├── src/todo/                    # Source code
│   ├── domain/                  # Entities (Task, TaskStatus)
│   ├── application/             # Use cases (business logic)
│   └── adapters/                # Interfaces (API, TUI, DB)
├── tests/                       # Unit tests
│   └── test_use_cases.py        # Business logic tests
├── bruno-coll/                  # Bruno collection (API tests)
├── .env                         # Environment variables (API_KEY)
├── pyproject.toml               # Poetry configuration
├── todo.db                      # SQLite database (auto-created)
└── notifications.txt            # Action log (auto-created)
```

---

## <i class='bx  bx-check-shield'></i>  Security

- **API Key**: Simple protection for external access
- **Validation**: Pydantic + use cases to prevent invalid data

---

## <i class='bx  bx-keyboard'></i>  TUI Shortcuts

| Key | Action |
|--------|--------|
| `a` | Add a task |
| `r` | Refresh the list |
| `Enter` | Open actions menu |
| `Ctrl+S` | Save (in modals) |
| `Ctrl+D` | Clear date (editing) |
| `Escape` | Cancel |
| `q` | Quit |
| `ctrl+p` | Open textual panel |

---

## <i class='bx  bx-future'></i>   Future improvements

- **JWT Authentication**: Replace simple API Key with JWT tokens for better security
- **User management**: Add user registration, login, and task ownership
- **Task sharing**: Enable collaboration between users
- **Priority levels**: Add task prioritization (low, medium, high)

---

## <i class='bx  bx-user-square'></i>  Author

This project was built by [Kylian Project](https://github.com/Kylian-Project)

---

## <i class='bx  bx-law'></i>  License

This project is licensed under the [MIT License](https://opensource.org/licenses/MIT).

---

## <i class='bx  bx-book-library'></i>  Resources

- [Textual Documentation](https://textual.textualize.io/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Rose Pine Theme](https://rosepinetheme.com/)
- [Posting (inspiration)](https://github.com/darrenburns/posting)

---

<div align="center">Built with ❤️ by Kylian Project</div>