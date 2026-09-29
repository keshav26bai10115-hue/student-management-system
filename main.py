import hashlib
import os
import sqlite3
import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk

import matplotlib

matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

DB_NAME = "sms_database.db"


# ==========================================
# DATABASE HANDLER & SECURITY
# ==========================================
def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def hash_password(password, salt=None):
    """PBKDF2 Password Hashing with Salt."""
    if salt is None:
        salt_bytes = os.urandom(16)
    else:
        salt_bytes = bytes.fromhex(salt)

    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt_bytes, 100000)
    return f"{salt_bytes.hex()}:{key.hex()}"


def verify_password(stored_password, provided_password):
    try:
        salt, key = stored_password.split(":")
        return hash_password(provided_password, salt) == stored_password
    except ValueError:
        return False


def init_db():
    with get_db_connection() as conn:
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL
            )
        """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS students (
                roll_no TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                course TEXT NOT NULL,
                email TEXT,
                gender TEXT,
                fee_status TEXT
            )
        """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS marks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                roll_no TEXT NOT NULL,
                subject TEXT NOT NULL,
                marks_obtained REAL NOT NULL,
                max_marks REAL NOT NULL,
                percentage REAL,
                grade TEXT,
                FOREIGN KEY (roll_no) REFERENCES students (roll_no) ON DELETE CASCADE
            )
        """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                roll_no TEXT NOT NULL,
                date TEXT NOT NULL,
                status TEXT NOT NULL,
                FOREIGN KEY (roll_no) REFERENCES students (roll_no) ON DELETE CASCADE
            )
        """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS activity_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                action TEXT NOT NULL,
                timestamp TEXT NOT NULL
            )
        """
        )

        # Force update default accounts with PBKDF2 hashed passwords
        admin_pass = hash_password("admin123")
        teacher_pass = hash_password("teacher123")

        cursor.execute(
            """
            INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)
            ON CONFLICT(username) DO UPDATE SET password_hash=excluded.password_hash
            """,
            ("admin", admin_pass, "Admin"),
        )
        cursor.execute(
            """
            INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)
            ON CONFLICT(username) DO UPDATE SET password_hash=excluded.password_hash
            """,
            ("teacher", teacher_pass, "Teacher"),
        )


def log_activity(username, action):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO activity_logs (username, action, timestamp) VALUES (?, ?, ?)",
            (username, action, now),
        )


# ==========================================
# LOGIN WINDOW
# ==========================================
class LoginWindow:

    def __init__(self, root):
        self.root = root
        self.root.title("SMS - Secure Login")
        self.root.geometry("380x300")
        self.root.resizable(False, False)

        tk.Label(
            root, text="Student Management System", font=("Arial", 14, "bold")
        ).pack(pady=15)

        frame = tk.Frame(root)
        frame.pack(pady=10)

        tk.Label(frame, text="Username:", font=("Arial", 10)).grid(
            row=0, column=0, sticky="w", pady=5
        )
        self.ent_username = tk.Entry(frame, width=22)
        self.ent_username.grid(row=0, column=1, pady=5)

        tk.Label(frame, text="Password:", font=("Arial", 10)).grid(
            row=1, column=0, sticky="w", pady=5
        )
        self.ent_password = tk.Entry(frame, show="*", width=22)
        self.ent_password.grid(row=1, column=1, pady=5)

        tk.Button(
            root,
            text="Login",
            command=self.login,
            width=15,
            bg="#4CAF50",
            fg="white",
            font=("Arial", 10, "bold"),
        ).pack(pady=15)
        tk.Label(
            root, text="Admin: admin/admin123 | Teacher: teacher/teacher123", fg="gray"
        ).pack()

    def login(self):
        username = self.ent_username.get().strip().lower()
        password = self.ent_password.get().strip()

        if not username or not password:
            messagebox.showerror("Error", "Please enter both credentials.")
            return

        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT password_hash, role FROM users WHERE LOWER(username)=?",
                (username,),
            )
            user = cursor.fetchone()

        if user and verify_password(user[0], password):
            role = user[1]
            log_activity(username, f"User logged in as {role}")
            
            # Clear login window widgets
            for widget in self.root.winfo_children():
                widget.destroy()
                
            # Launch main dashboard
            Dashboard(self.root, username, role)
        else:
            messagebox.showerror("Error", "Invalid credentials.")


# ==========================================
# MAIN DASHBOARD
# ==========================================
class Dashboard:

    def __init__(self, root, username, role):
        self.root = root
        self.username = username
        self.role = role
        self.root.title(
            f"Student Management System - Logged in: {self.username} ({self.role})"
        )
        self.root.geometry("980x640")
        self.root.resizable(True, True)

        title_frame = tk.Frame(self.root, bg="#2196F3")
        title_frame.pack(fill="x")
        tk.Label(
            title_frame,
            text=f"Student Management System ({self.role} Panel)",
            font=("Arial", 16, "bold"),
            bg="#2196F3",
            fg="white",
            pady=10,
        ).pack()

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        self.tab_students = ttk.Frame(self.notebook)
        self.tab_academics = ttk.Frame(self.notebook)
        self.tab_attendance = ttk.Frame(self.notebook)
        self.tab_analytics = ttk.Frame(self.notebook)
        self.tab_security = ttk.Frame(self.notebook)

        self.notebook.add(self.tab_students, text="Core Records")
        self.notebook.add(self.tab_academics, text="Academics")
        self.notebook.add(self.tab_attendance, text="Attendance")
        self.notebook.add(self.tab_analytics, text="Data Analytics")
        self.notebook.add(self.tab_security, text="Security & Audit Logs")

        self.setup_students_tab()
        self.setup_academics_tab()
        self.setup_attendance_tab()
        self.setup_analytics_tab()
        self.setup_security_tab()

        self.refresh_student_dropdowns()

    def create_treeview(self, parent, columns, headings):
        scroll_y = ttk.Scrollbar(parent, orient="vertical")
        scroll_x = ttk.Scrollbar(parent, orient="horizontal")

        tree = ttk.Treeview(
            parent,
            columns=columns,
            show="headings",
            yscrollcommand=scroll_y.set,
            xscrollcommand=scroll_x.set,
        )
        scroll_y.pack(side="right", fill="y")
        scroll_x.pack(side="bottom", fill="x")
        scroll_y.config(command=tree.yview)
        scroll_x.config(command=tree.xview)

        for col, head in zip(columns, headings):
            tree.heading(col, text=head)
            tree.column(col, width=100)

        tree.pack(fill="both", expand=True)
        return tree

    # ------------------------------------------
    # TAB 1: CORE STUDENTS
    # ------------------------------------------
    def setup_students_tab(self):
        form_frame = tk.LabelFrame(
            self.tab_students, text="Student Info", font=("Arial", 10, "bold")
        )
        form_frame.place(x=10, y=10, width=280, height=500)

        fields = [
            ("Roll No:", "roll_no"),
            ("Name:", "name"),
            ("Course:", "course"),
            ("Email:", "email"),
        ]
        self.student_entries = {}

        for i, (label_text, field_name) in enumerate(fields):
            tk.Label(form_frame, text=label_text).grid(
                row=i, column=0, sticky="w", padx=8, pady=8
            )
            ent = tk.Entry(form_frame, width=18)
            ent.grid(row=i, column=1, padx=8, pady=8)
            self.student_entries[field_name] = ent

        tk.Label(form_frame, text="Gender:").grid(
            row=4, column=0, sticky="w", padx=8, pady=8
        )
        self.combo_gender = ttk.Combobox(
            form_frame, values=["Male", "Female", "Other"], width=15, state="readonly"
        )
        self.combo_gender.grid(row=4, column=1, padx=8, pady=8)

        tk.Label(form_frame, text="Fee Status:").grid(
            row=5, column=0, sticky="w", padx=8, pady=8
        )
        self.combo_fee = ttk.Combobox(
            form_frame, values=["Paid", "Pending"], width=15, state="readonly"
        )
        self.combo_fee.grid(row=5, column=1, padx=8, pady=8)

        if self.role == "Admin":
            btn_frame = tk.Frame(form_frame)
            btn_frame.grid(row=6, columnspan=2, pady=15)

            tk.Button(
                btn_frame,
                text="Add",
                command=self.add_student,
                width=7,
                bg="#4CAF50",
                fg="white",
            ).grid(row=0, column=0, padx=2)
            tk.Button(
                btn_frame,
                text="Update",
                command=self.update_student,
                width=7,
                bg="#FF9800",
                fg="white",
            ).grid(row=0, column=1, padx=2)
            tk.Button(
                btn_frame,
                text="Delete",
                command=self.delete_student,
                width=7,
                bg="#F44336",
                fg="white",
            ).grid(row=0, column=2, padx=2)
            tk.Button(
                btn_frame,
                text="Clear",
                command=self.clear_student_entries,
                width=24,
                bg="#9E9E9E",
                fg="white",
            ).grid(row=1, columnspan=3, pady=5)
        else:
            tk.Label(
                form_frame,
                text="[Read-Only Mode]",
                fg="red",
                font=("Arial", 10, "italic"),
            ).grid(row=6, columnspan=2, pady=20)

        table_frame = tk.Frame(self.tab_students)
        table_frame.place(x=300, y=10, width=640, height=500)

        cols = ("roll_no", "name", "course", "email", "gender", "fee_status")
        heads = ("Roll No", "Name", "Course", "Email", "Gender", "Fee Status")
        self.student_table = self.create_treeview(table_frame, cols, heads)
        self.student_table.bind("<ButtonRelease-1>", self.get_student_cursor)

        self.fetch_students()

    def add_student(self):
        data = (
            self.student_entries["roll_no"].get().strip(),
            self.student_entries["name"].get().strip(),
            self.student_entries["course"].get().strip(),
            self.student_entries["email"].get().strip(),
            self.combo_gender.get(),
            self.combo_fee.get(),
        )
        if not data[0] or not data[1]:
            messagebox.showerror("Error", "Roll No and Name are mandatory fields.")
            return
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO students VALUES (?, ?, ?, ?, ?, ?)", data
                )

            log_activity(self.username, f"Added student: {data[1]} (Roll: {data[0]})")
            self.fetch_students()
            self.refresh_student_dropdowns()
            self.clear_student_entries()
            messagebox.showinfo("Success", "Student added successfully!")
        except sqlite3.IntegrityError:
            messagebox.showerror(
                "Error", "A student with this Roll No already exists."
            )

    def fetch_students(self):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM students")
            rows = cursor.fetchall()

        self.student_table.delete(*self.student_table.get_children())
        for row in rows:
            self.student_table.insert("", "end", values=row)

    def clear_student_entries(self):
        for entry in self.student_entries.values():
            entry.delete(0, tk.END)
        self.combo_gender.set("")
        self.combo_fee.set("")

    def get_student_cursor(self, event):
        cursor_row = self.student_table.focus()
        contents = self.student_table.item(cursor_row)
        row = contents.get("values")
        if row:
            self.clear_student_entries()
            self.student_entries["roll_no"].insert(0, row[0])
            self.student_entries["name"].insert(0, row[1])
            self.student_entries["course"].insert(0, row[2])
            self.student_entries["email"].insert(0, row[3])
            self.combo_gender.set(row[4])
            self.combo_fee.set(row[5])

    def update_student(self):
        data = (
            self.student_entries["name"].get().strip(),
            self.student_entries["course"].get().strip(),
            self.student_entries["email"].get().strip(),
            self.combo_gender.get(),
            self.combo_fee.get(),
            self.student_entries["roll_no"].get().strip(),
        )
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE students SET name=?, course=?, email=?, gender=?, fee_status=? WHERE roll_no=?",
                data,
            )

        log_activity(self.username, f"Updated student Roll No: {data[5]}")
        self.fetch_students()
        self.clear_student_entries()
        messagebox.showinfo("Success", "Record updated successfully.")

    def delete_student(self):
        roll_no = self.student_entries["roll_no"].get().strip()
        if not roll_no:
            messagebox.showerror("Error", "Select a record to delete.")
            return

        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM students WHERE roll_no=?", (roll_no,))

        log_activity(self.username, f"Deleted student Roll No: {roll_no}")
        self.fetch_students()
        self.refresh_student_dropdowns()
        self.clear_student_entries()
        messagebox.showinfo("Success", "Record deleted successfully.")

    # ------------------------------------------
    # TAB 2: ACADEMICS
    # ------------------------------------------
    def setup_academics_tab(self):
        form_frame = tk.LabelFrame(
            self.tab_academics, text="Grade Entry", font=("Arial", 10, "bold")
        )
        form_frame.place(x=10, y=10, width=280, height=500)

        tk.Label(form_frame, text="Select Roll No:").grid(
            row=0, column=0, sticky="w", padx=8, pady=10
        )
        self.combo_marks_roll = ttk.Combobox(form_frame, width=15, state="readonly")
        self.combo_marks_roll.grid(row=0, column=1, padx=8, pady=10)

        tk.Label(form_frame, text="Subject:").grid(
            row=1, column=0, sticky="w", padx=8, pady=10
        )
        self.ent_subject = tk.Entry(form_frame, width=18)
        self.ent_subject.grid(row=1, column=1, padx=8, pady=10)

        tk.Label(form_frame, text="Marks Obtained:").grid(
            row=2, column=0, sticky="w", padx=8, pady=10
        )
        self.ent_marks = tk.Entry(form_frame, width=18)
        self.ent_marks.grid(row=2, column=1, padx=8, pady=10)

        tk.Label(form_frame, text="Max Marks:").grid(
            row=3, column=0, sticky="w", padx=8, pady=10
        )
        self.ent_max_marks = tk.Entry(form_frame, width=18)
        self.ent_max_marks.insert(0, "100")
        self.ent_max_marks.grid(row=3, column=1, padx=8, pady=10)

        if self.role in ("Admin", "Teacher"):
            tk.Button(
                form_frame,
                text="Save Grade",
                command=self.add_marks,
                bg="#4CAF50",
                fg="white",
                width=22,
            ).grid(row=4, columnspan=2, pady=20)

        table_frame = tk.Frame(self.tab_academics)
        table_frame.place(x=300, y=10, width=640, height=500)

        cols = (
            "id",
            "roll_no",
            "subject",
            "marks",
            "max_marks",
            "percentage",
            "grade",
        )
        heads = (
            "ID",
            "Roll No",
            "Subject",
            "Obtained",
            "Max",
            "Percentage",
            "Grade",
        )
        self.marks_table = self.create_treeview(table_frame, cols, heads)

        self.fetch_marks()

    def add_marks(self):
        roll_no = self.combo_marks_roll.get()
        subject = self.ent_subject.get().strip()
        try:
            obtained = float(self.ent_marks.get().strip())
            max_m = float(self.ent_max_marks.get().strip())
        except ValueError:
            messagebox.showerror("Error", "Enter valid numbers for marks.")
            return

        if max_m <= 0:
            messagebox.showerror("Error", "Max marks must be greater than zero.")
            return

        if obtained < 0 or obtained > max_m:
            messagebox.showerror(
                "Error", "Obtained marks must be between 0 and Max Marks."
            )
            return

        if not roll_no or not subject:
            messagebox.showerror("Error", "Fill in all fields.")
            return

        pct = round((obtained / max_m) * 100, 2)
        grade = (
            "A" if pct >= 85 else "B" if pct >= 70 else "C" if pct >= 50 else "F"
        )

        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO marks (roll_no, subject, marks_obtained, max_marks, percentage, grade) VALUES (?, ?, ?, ?, ?, ?)",
                (roll_no, subject, obtained, max_m, pct, grade),
            )

        log_activity(
            self.username,
            f"Logged grade '{grade}' for Roll: {roll_no}, Subject: {subject}",
        )
        self.fetch_marks()
        self.ent_subject.delete(0, tk.END)
        self.ent_marks.delete(0, tk.END)
        messagebox.showinfo("Success", "Grade recorded.")

    def fetch_marks(self):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM marks")
            rows = cursor.fetchall()

        self.marks_table.delete(*self.marks_table.get_children())
        for row in rows:
            self.marks_table.insert("", "end", values=row)

    # ------------------------------------------
    # TAB 3: ATTENDANCE
    # ------------------------------------------
    def setup_attendance_tab(self):
        form_frame = tk.LabelFrame(
            self.tab_attendance, text="Mark Attendance", font=("Arial", 10, "bold")
        )
        form_frame.place(x=10, y=10, width=280, height=500)

        tk.Label(form_frame, text="Select Roll No:").grid(
            row=0, column=0, sticky="w", padx=8, pady=10
        )
        self.combo_att_roll = ttk.Combobox(form_frame, width=15, state="readonly")
        self.combo_att_roll.grid(row=0, column=1, padx=8, pady=10)

        tk.Label(form_frame, text="Date (YYYY-MM-DD):").grid(
            row=1, column=0, sticky="w", padx=8, pady=10
        )
        self.ent_att_date = tk.Entry(form_frame, width=18)
        self.ent_att_date.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.ent_att_date.grid(row=1, column=1, padx=8, pady=10)

        tk.Label(form_frame, text="Status:").grid(
            row=2, column=0, sticky="w", padx=8, pady=10
        )
        self.combo_att_status = ttk.Combobox(
            form_frame,
            values=["Present", "Absent", "Late"],
            width=15,
            state="readonly",
        )
        self.combo_att_status.grid(row=2, column=1, padx=8, pady=10)

        if self.role in ("Admin", "Teacher"):
            tk.Button(
                form_frame,
                text="Save Attendance",
                command=self.add_attendance,
                bg="#2196F3",
                fg="white",
                width=22,
            ).grid(row=3, columnspan=2, pady=20)

        table_frame = tk.Frame(self.tab_attendance)
        table_frame.place(x=300, y=10, width=640, height=500)

        cols = ("id", "roll_no", "date", "status")
        heads = ("ID", "Roll No", "Date", "Status")
        self.att_table = self.create_treeview(table_frame, cols, heads)

        self.fetch_attendance()

    def add_attendance(self):
        roll_no = self.combo_att_roll.get()
        date_str = self.ent_att_date.get().strip()
        status = self.combo_att_status.get()

        if not roll_no or not date_str or not status:
            messagebox.showerror("Error", "All fields are required.")
            return

        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO attendance (roll_no, date, status) VALUES (?, ?, ?)",
                (roll_no, date_str, status),
            )

        log_activity(
            self.username, f"Marked {status} for Roll: {roll_no} on {date_str}"
        )
        self.fetch_attendance()
        messagebox.showinfo("Success", "Attendance logged.")

    def fetch_attendance(self):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM attendance")
            rows = cursor.fetchall()

        self.att_table.delete(*self.att_table.get_children())
        for row in rows:
            self.att_table.insert("", "end", values=row)

    # ------------------------------------------
    # TAB 4: DATA ANALYTICS
    # ------------------------------------------
    def setup_analytics_tab(self):
        tk.Button(
            self.tab_analytics,
            text="Refresh Visualizations",
            command=self.render_charts,
            bg="#2196F3",
            fg="white",
            font=("Arial", 10, "bold"),
        ).pack(pady=10)

        self.chart_frame = tk.Frame(self.tab_analytics)
        self.chart_frame.pack(fill="both", expand=True)

        self.render_charts()

    def render_charts(self):
        for widget in self.chart_frame.winfo_children():
            widget.destroy()

        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT grade, COUNT(*) FROM marks GROUP BY grade ORDER BY grade"
            )
            grade_data = dict(cursor.fetchall())

            cursor.execute(
                "SELECT status, COUNT(*) FROM attendance GROUP BY status"
            )
            att_data = dict(cursor.fetchall())

        fig = Figure(figsize=(9, 4), dpi=100)

        ax1 = fig.add_subplot(121)
        grades = ["A", "B", "C", "F"]
        counts = [grade_data.get(g, 0) for g in grades]
        ax1.bar(grades, counts, color=["#4CAF50", "#2196F3", "#FF9800", "#F44336"])
        ax1.set_title("Grade Distribution")
        ax1.set_xlabel("Grade")
        ax1.set_ylabel("Number of Students")

        ax2 = fig.add_subplot(122)
        att_labels = list(att_data.keys()) if att_data else ["No Data"]
        att_counts = list(att_data.values()) if att_data else [1]
        ax2.pie(att_counts, labels=att_labels, autopct="%1.1f%%", startangle=90)
        ax2.set_title("Overall Attendance Spread")

        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    # ------------------------------------------
    # TAB 5: SECURITY & AUDIT LOGS
    # ------------------------------------------
    def setup_security_tab(self):
        tk.Label(
            self.tab_security,
            text="System Audit & Activity Logs",
            font=("Arial", 12, "bold"),
        ).pack(pady=10)

        log_frame = tk.Frame(self.tab_security)
        log_frame.pack(fill="both", expand=True, padx=20, pady=10)

        cols = ("id", "username", "action", "timestamp")
        heads = ("Log ID", "User", "Action Executed", "Timestamp")
        self.log_table = self.create_treeview(log_frame, cols, heads)

        tk.Button(
            self.tab_security,
            text="Refresh Audit Log",
            command=self.fetch_logs,
            bg="#9E9E9E",
            fg="white",
        ).pack(pady=10)

        self.fetch_logs()

    def fetch_logs(self):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM activity_logs ORDER BY id DESC LIMIT 50"
            )
            rows = cursor.fetchall()

        self.log_table.delete(*self.log_table.get_children())
        for row in rows:
            self.log_table.insert("", "end", values=row)

    def refresh_student_dropdowns(self):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT roll_no FROM students")
            rolls = [r[0] for r in cursor.fetchall()]

        if hasattr(self, "combo_marks_roll"):
            self.combo_marks_roll["values"] = rolls
        if hasattr(self, "combo_att_roll"):
            self.combo_att_roll["values"] = rolls


# ==========================================
# MAIN LAUNCHER
# ==========================================
if __name__ == "__main__":
    init_db()
    root = tk.Tk()
    app = LoginWindow(root)
    root.mainloop()
