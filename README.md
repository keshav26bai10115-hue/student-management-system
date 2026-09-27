# Student Management System (SMS)

A desktop application for managing student records, academics, attendance, fee status, and analytics, with secure role-based login for **Admin** and **Teacher** users.

Built with **Python**, **Tkinter** (interface), **SQLite** (database), and **Matplotlib** (charts).

---

## Features

- **Secure Login** — role-based access for Admin and Teacher accounts, with passwords stored using salted PBKDF2-SHA256 hashing (not plain text).
- **Student Records (Core Records tab)** — add, update, delete, and view student details: roll number, name, course, email, gender, and fee status.
- **Academics tab** — record subject-wise marks per student; the system auto-calculates percentage and letter grade (A/B/C/F).
- **Attendance tab** — mark daily attendance per student (Present / Absent / Late) and view full attendance history.
- **Data Analytics tab** — visual charts (bar chart of grade distribution, pie chart of attendance spread) generated live from the database using Matplotlib.
- **Security & Audit Logs tab** — every significant action (login, add/update/delete student, marks entry, attendance entry) is logged with username and timestamp.
- **Role-based permissions** — Admin has full read/write access; Teacher has restricted access (e.g., cannot delete student records).

---

## Tech Stack

| Component      | Technology              |
|-----------------|--------------------------|
| Language        | Python 3.8+              |
| GUI             | Tkinter (Python standard library) |
| Database        | SQLite3 (Python standard library) |
| Charts          | Matplotlib                |
| Security        | hashlib (PBKDF2-HMAC-SHA256) |

---

## Prerequisites

- **Python 3.8 or higher** installed on your machine.
  - Check with: `python3 --version` (or `python --version` on Windows)
- **Tkinter**: bundled with Python on Windows and macOS. On some **Linux** distributions it must be installed separately:
  ```bash
  sudo apt-get update
  sudo apt-get install python3-tk
  ```
- A terminal / command prompt.

---

## Setup Instructions

### 1. Clone the repository

```bash
git clone https://github.com/<your-username>/<your-repo-name>.git
cd <your-repo-name>
```

### 2. Create a virtual environment (recommended)

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

This installs Matplotlib. (Tkinter and SQLite3 come with Python itself — no install needed.)

### 4. Run the application

```bash
python main.py
```

On first run, the app automatically creates a local SQLite database file named `sms_database.db` in the project folder and sets up all required tables and two default user accounts — no manual configuration needed.

---

## Default Login Credentials

| Role     | Username | Password    |
|----------|----------|-------------|
| Admin    | `admin`  | `admin123`  |
| Teacher  | `teacher`| `teacher123`|

These are created automatically the first time you run `main.py`.

---

## Project Structure

```
.
├── main.py              # Application entry point (login, dashboard, all tabs/logic)
├── requirements.txt      # Python dependencies
├── .gitignore            # Files/folders excluded from version control
├── README.md             # This file
└── sms_database.db       # Auto-generated on first run (not committed to git)
```

---

## How to Use

1. Run `python main.py`.
2. Log in as Admin or Teacher using the credentials above.
3. Use the tabs across the top of the dashboard:
   - **Core Records** — add/update/delete student information (Admin only for write actions).
   - **Academics** — enter subject marks; grade and percentage are calculated automatically.
   - **Attendance** — mark and view daily attendance.
   - **Data Analytics** — click "Refresh Visualizations" to view up-to-date charts.
   - **Security & Audit Logs** — view a history of actions performed by users.

---

## Notes

- The database file (`sms_database.db`) is created automatically and is excluded from version control via `.gitignore`. Deleting it will reset all data on next run.
- Passwords are never stored in plain text; they are hashed using PBKDF2-HMAC-SHA256 with a random salt per user.
- This project is a course assignment submission and is intended to be run locally via the command shown above.
