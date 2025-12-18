# Event Organizer Web Application

This repository contains a full-stack web application for managing dance events. The application is built with **FastAPI** on the backend and plain **HTML/CSS/JavaScript** on the frontend. It follows the architecture, data models, and workflows described in the provided Software Design Documents (SDDs).

## Features

* **Authentication** – Users must log in with a username and password to access the app. A default administrator account is seeded on first run.
* **CRUD Operations** – Manage Rooms, Caller/Cuers, Events, and MC assignments. Create, edit, and delete records with validation rules enforced server‑side.
* **Home Page** – Switch between views for each entity, view records in a simple table, and open modals to create or edit items.
* **Presentation Mode** – Select a room and display its upcoming events on a continuously refreshing schedule board optimized for large displays and elderly users.
* **Caller Lounge Board** – A dedicated presentation view for callers showing the combined schedule across every room with live auto-scrolling.
* **Responsive Design** – Large, high‑contrast typography and a calm corporate palette ensure readability on both tablets and projectors.

## Project Structure

```
.
├── main.py                # Entry point for the FastAPI application
├── DAL/                   # Data access layer (SQLite helper & Pydantic schemas)
│   ├── db.py
│   ├── models.py          # (Unused legacy SQLAlchemy models)
│   └── schemas.py
├── Services/              # Business logic for each entity
├── Controllers/           # Controller functions converting models to schemas
├── Routes/                # FastAPI routers for each resource
├── Database/              # Placeholder package (database lives at /home/site/Database)
├── Public/                # Frontend static files served by FastAPI
│   ├── index.html         # Home page
│   ├── login.html         # Login page
│   ├── presentation.html  # Presentation page
│   ├── styles.css         # Shared styles
│   ├── app.js             # JavaScript for the home page
│   └── presentation.js    # JavaScript for the presentation page
├── requirements.txt       # Python dependencies
└── README.md
```

## Running the Application Locally

1. **Install dependencies**

   The application relies only on `fastapi` and `uvicorn`, which are
   already included in this environment. If you are running
   elsewhere, install the requirements:

   ```bash
   pip install fastapi uvicorn
   ```

2. **Start the server**

   ```bash
   uvicorn main:app --reload
   ```

   The application will start on `http://127.0.0.1:8000`. Static frontend files are served from the `Public` directory.

3. **Log in**

   Navigate to `http://127.0.0.1:8000/login`. The application seeds three accounts on startup:

   * `master` — administrator role. The password comes from the `INITIAL_ADMIN_PW` environment variable
   * `attendee` — read-only attendee role. Set the password with the required `ATTENDEE_PASS` environment variable.
   * `caller` — read-only caller lounge role. Set the password with the required `CALLER_PASS` environment variable.

   Ensure `ATTENDEE_PASS` and `CALLER_PASS` are defined before starting the server so the accounts are provisioned correctly.


4. **Using the App**

   * **Home Page:** After logging in, you’ll be redirected to the home page where you can browse and manage Rooms, Caller/Cuers, Events, and MC assignments. Use the “View” dropdown to switch between entities. The “Create” dropdown opens a modal to add a new record.
   * **Editing & Deleting:** Each row has “Edit” and “Delete” buttons. Editing opens the same modal prefilled with data. Deletion prompts for confirmation.
   * **Presentation Page:** Click “Presentation” in the top bar to view the presentation board. Select a room to see its upcoming events and current MC. The board refreshes automatically every five minutes.
   * **Caller Lounge Board:** Click “Caller Board” in the top bar (visible to master and caller roles) to monitor every event across all rooms with auto-scrolling and fullscreen options.
   * **Logout:** Click “Logout” to clear your session and return to the login screen.

## Deployment Notes

This application is designed to run in **Azure WebApp Service**. The entry
point is `main.py`, which is automatically used by Uvicorn when
deploying. Static files under the `Public` directory are served by
FastAPI via the `/static` mount point, and the HTML pages are available
at `/`, `/login`, and `/presentation`. The SQLite database is stored at
`/home/site/Database/database.db`; the application will create the
directory and database file automatically on startup if they do not
already exist so the data persists across deployments.

## Extending the Application

The current implementation provides a foundation inspired by the supplied
SDDs. Due to environment restrictions (no external database ORM or
cryptography libraries), the backend uses the built‑in `sqlite3`
module and a simple token store for authentication. To fully match
all original requirements (e.g. advanced time‑bound room descriptions,
optimistic concurrency with version fields, paginated search with sort
fields, and comprehensive accessibility), additional development
would be required. The modular architecture (DAL → Services →
Controllers → Routes) makes it straightforward to add new features
while maintaining a clean separation of concerns.

## License

This project is provided for demonstration purposes and does not include any warranty. Feel free to adapt or extend it for your own needs.
