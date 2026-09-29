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

DATABASE_FILE = "sms_database.db"


def open_connection():
    c = sqlite3.connect(DATABASE_FILE)
    c.execute("PRAGMA foreign_keys = ON;")
    return c


def create_password_hash(raw_pwd, salt=None):
    if not salt:
        s_bytes = os.urandom(16)
    else:
        s_bytes = bytes.fromhex(salt)

    derived = hashlib.pbkdf2_hmac("sha256", raw_pwd.encode("utf-8"), s_bytes, 100000)
    return f"{s_bytes.hex()}:{derived.hex()}"


def check_password(db_hash, user_input):
    try:
        salt, _ = db_hash.split(":")
        return create_password_hash(user_input, salt) == db_hash
    except Exception:
        return False


def setup_tables():
    with open_connection() as conn:
        db = conn.cursor()

        db.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL
            )
        """
        )

        db.execute(
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

        db.execute(
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

        db.execute(
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

        db.execute(
            """
            CREATE TABLE IF NOT EXISTS activity_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                action TEXT NOT NULL,
                timestamp TEXT NOT NULL
            )
        """
        )

        # Default system accounts
        p_admin = create_password_hash("admin123")
        p_teacher = create_password_hash("teacher123")

        db.execute(
            """
            INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)
            ON CONFLICT(username) DO UPDATE SET password_hash=excluded.password_hash
            """,
            ("admin", p_admin, "Admin"),
        )
        db.execute(
            """
            INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)
            ON CONFLICT(username) DO UPDATE SET password_hash=excluded.password_hash
            """,
            ("teacher", p_teacher, "Teacher"),
        )


def record_log(user, details):
    dt_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO activity_logs (username, action, timestamp) VALUES (?, ?, ?)",
            (user, details, dt_now),
        )


class LoginView:

    def __init__(self, master):
        self.win = master
        self.win.title("SMS - Login")
        self.win.geometry("380x300")
        self.win.resizable(False, False)

        tk.Label(
            self.win, text="Student Management System", font=("Arial", 14, "bold")
        ).pack(pady=15)

        pnl = tk.Frame(self.win)
        pnl.pack(pady=10)

        tk.Label(pnl, text="Username:", font=("Arial", 10)).grid(
            row=0, column=0, sticky="w", pady=5
        )
        self.u_input = tk.Entry(pnl, width=22)
        self.u_input.grid(row=0, column=1, pady=5)

        tk.Label(pnl, text="Password:", font=("Arial", 10)).grid(
            row=1, column=0, sticky="w", pady=5
        )
        self.p_input = tk.Entry(pnl, show="*", width=22)
        self.p_input.grid(row=1, column=1, pady=5)

        tk.Button(
            self.win,
            text="Login",
            command=self.handle_login,
            width=15,
            bg="#4CAF50",
            fg="white",
            font=("Arial", 10, "bold"),
        ).pack(pady=15)

        tk.Label(
            self.win,
            text="Admin: admin/admin123 | Teacher: teacher/teacher123",
            fg="gray",
        ).pack()

    def handle_login(self):
        usr = self.u_input.get().strip().lower()
        pwd = self.p_input.get().strip()

        if not usr or not pwd:
            messagebox.showerror("Error", "Please enter both credentials.")
            return

        with open_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT password_hash, role FROM users WHERE LOWER(username)=?", (usr,)
            )
            account = cursor.fetchone()

        if account and check_password(account[0], pwd):
            usr_role = account[1]
            record_log(usr, f"User logged in as {usr_role}")

            for child in self.win.winfo_children():
                child.destroy()

            MainApp(self.win, usr, usr_role)
        else:
            messagebox.showerror("Error", "Invalid credentials.")


class MainApp:

    def __init__(self, root, username, role):
        self.root = root
        self.curr_user = username
        self.curr_role = role
        self.root.title(
            f"Student Management System - {self.curr_user} ({self.curr_role})"
        )
        self.root.geometry("980x640")

        header = tk.Frame(self.root, bg="#2196F3")
        header.pack(fill="x")
        tk.Label(
            header,
            text=f"Student Management System ({self.curr_role} Panel)",
            font=("Arial", 16, "bold"),
            bg="#2196F3",
            fg="white",
            pady=10,
        ).pack()

        self.tabs = ttk.Notebook(self.root)
        self.tabs.pack(fill="both", expand=True, padx=10, pady=10)

        self.tab_st = ttk.Frame(self.tabs)
        self.tab_ac = ttk.Frame(self.tabs)
        self.tab_at = ttk.Frame(self.tabs)
        self.tab_an = ttk.Frame(self.tabs)
        self.tab_sc = ttk.Frame(self.tabs)

        self.tabs.add(self.tab_st, text="Core Records")
        self.tabs.add(self.tab_ac, text="Academics")
        self.tabs.add(self.tab_at, text="Attendance")
        self.tabs.add(self.tab_an, text="Data Analytics")
        self.tabs.add(self.tab_sc, text="Security & Audit Logs")

        self.build_students_panel()
        self.build_academics_panel()
        self.build_attendance_panel()
        self.build_analytics_panel()
        self.build_security_panel()

        self.update_roll_lists()

    def build_grid_view(self, parent_frame, col_keys, col_labels):
        sy = ttk.Scrollbar(parent_frame, orient="vertical")
        sx = ttk.Scrollbar(parent_frame, orient="horizontal")

        view = ttk.Treeview(
            parent_frame,
            columns=col_keys,
            show="headings",
            yscrollcommand=sy.set,
            xscrollcommand=sx.set,
        )
        sy.pack(side="right", fill="y")
        sx.pack(side="bottom", fill="x")
        sy.config(command=view.yview)
        sx.config(command=view.xview)

        for k, l in zip(col_keys, col_labels):
            view.heading(k, text=l)
            view.column(k, width=100)

        view.pack(fill="both", expand=True)
        return view

    # 1. Students Panel
    def build_students_panel(self):
        side_box = tk.LabelFrame(
            self.tab_st, text="Student Info", font=("Arial", 10, "bold")
        )
        side_box.place(x=10, y=10, width=280, height=500)

        field_names = [
            ("Roll No:", "roll_no"),
            ("Name:", "name"),
            ("Course:", "course"),
            ("Email:", "email"),
        ]
        self.st_inputs = {}

        for idx, (label, key) in enumerate(field_names):
            tk.Label(side_box, text=label).grid(
                row=idx, column=0, sticky="w", padx=8, pady=8
            )
            inp = tk.Entry(side_box, width=18)
            inp.grid(row=idx, column=1, padx=8, pady=8)
            self.st_inputs[key] = inp

        tk.Label(side_box, text="Gender:").grid(
            row=4, column=0, sticky="w", padx=8, pady=8
        )
        self.sel_gender = ttk.Combobox(
            side_box, values=["Male", "Female", "Other"], width=15, state="readonly"
        )
        self.sel_gender.grid(row=4, column=1, padx=8, pady=8)

        tk.Label(side_box, text="Fee Status:").grid(
            row=5, column=0, sticky="w", padx=8, pady=8
        )
        self.sel_fee = ttk.Combobox(
            side_box, values=["Paid", "Pending"], width=15, state="readonly"
        )
        self.sel_fee.grid(row=5, column=1, padx=8, pady=8)

        if self.curr_role == "Admin":
            actions = tk.Frame(side_box)
            actions.grid(row=6, columnspan=2, pady=15)

            tk.Button(
                actions,
                text="Add",
                command=self.save_new_student,
                width=7,
                bg="#4CAF50",
                fg="white",
            ).grid(row=0, column=0, padx=2)
            tk.Button(
                actions,
                text="Update",
                command=self.edit_student_record,
                width=7,
                bg="#FF9800",
                fg="white",
            ).grid(row=0, column=1, padx=2)
            tk.Button(
                actions,
                text="Delete",
                command=self.remove_student,
                width=7,
                bg="#F44336",
                fg="white",
            ).grid(row=0, column=2, padx=2)
            tk.Button(
                actions,
                text="Clear",
                command=self.reset_student_form,
                width=24,
                bg="#9E9E9E",
                fg="white",
            ).grid(row=1, columnspan=3, pady=5)
        else:
            tk.Label(
                side_box,
                text="[Read-Only Mode]",
                fg="red",
                font=("Arial", 10, "italic"),
            ).grid(row=6, columnspan=2, pady=20)

        data_container = tk.Frame(self.tab_st)
        data_container.place(x=300, y=10, width=640, height=500)

        k_list = ("roll_no", "name", "course", "email", "gender", "fee_status")
        l_list = ("Roll No", "Name", "Course", "Email", "Gender", "Fee Status")
        self.tbl_students = self.build_grid_view(data_container, k_list, l_list)
        self.tbl_students.bind("<ButtonRelease-1>", self.on_select_student)

        self.load_students_data()

    def save_new_student(self):
        payload = (
            self.st_inputs["roll_no"].get().strip(),
            self.st_inputs["name"].get().strip(),
            self.st_inputs["course"].get().strip(),
            self.st_inputs["email"].get().strip(),
            self.sel_gender.get(),
            self.sel_fee.get(),
        )
        if not payload[0] or not payload[1]:
            messagebox.showerror("Error", "Roll No and Name are mandatory fields.")
            return
        try:
            with open_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO students VALUES (?, ?, ?, ?, ?, ?)", payload
                )

            record_log(
                self.curr_user, f"Added student: {payload[1]} (Roll: {payload[0]})"
            )
            self.load_students_data()
            self.update_roll_lists()
            self.reset_student_form()
            messagebox.showinfo("Success", "Student added successfully!")
        except sqlite3.IntegrityError:
            messagebox.showerror(
                "Error", "A student with this Roll No already exists."
            )

    def load_students_data(self):
        with open_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM students")
            records = cursor.fetchall()

        self.tbl_students.delete(*self.tbl_students.get_children())
        for r in records:
            self.tbl_students.insert("", "end", values=r)

    def reset_student_form(self):
        for box in self.st_inputs.values():
            box.delete(0, tk.END)
        self.sel_gender.set("")
        self.sel_fee.set("")

    def on_select_student(self, event):
        row_id = self.tbl_students.focus()
        data = self.tbl_students.item(row_id).get("values")
        if data:
            self.reset_student_form()
            self.st_inputs["roll_no"].insert(0, data[0])
            self.st_inputs["name"].insert(0, data[1])
            self.st_inputs["course"].insert(0, data[2])
            self.st_inputs["email"].insert(0, data[3])
            self.sel_gender.set(data[4])
            self.sel_fee.set(data[5])

    def edit_student_record(self):
        payload = (
            self.st_inputs["name"].get().strip(),
            self.st_inputs["course"].get().strip(),
            self.st_inputs["email"].get().strip(),
            self.sel_gender.get(),
            self.sel_fee.get(),
            self.st_inputs["roll_no"].get().strip(),
        )
        with open_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE students SET name=?, course=?, email=?, gender=?, fee_status=? WHERE roll_no=?",
                payload,
            )

        record_log(self.curr_user, f"Updated student Roll No: {payload[5]}")
        self.load_students_data()
        self.reset_student_form()
        messagebox.showinfo("Success", "Record updated successfully.")

    def remove_student(self):
        r_num = self.st_inputs["roll_no"].get().strip()
        if not r_num:
            messagebox.showerror("Error", "Select a record to delete.")
            return

        with open_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM students WHERE roll_no=?", (r_num,))

        record_log(self.curr_user, f"Deleted student Roll No: {r_num}")
        self.load_students_data()
        self.update_roll_lists()
        self.reset_student_form()
        messagebox.showinfo("Success", "Record deleted successfully.")

    # 2. Academics Panel
    def build_academics_panel(self):
        side_box = tk.LabelFrame(
            self.tab_ac, text="Grade Entry", font=("Arial", 10, "bold")
        )
        side_box.place(x=10, y=10, width=280, height=500)

        tk.Label(side_box, text="Select Roll No:").grid(
            row=0, column=0, sticky="w", padx=8, pady=10
        )
        self.dd_marks_roll = ttk.Combobox(side_box, width=15, state="readonly")
        self.dd_marks_roll.grid(row=0, column=1, padx=8, pady=10)

        tk.Label(side_box, text="Subject:").grid(
            row=1, column=0, sticky="w", padx=8, pady=10
        )
        self.txt_subject = tk.Entry(side_box, width=18)
        self.txt_subject.grid(row=1, column=1, padx=8, pady=10)

        tk.Label(side_box, text="Marks Obtained:").grid(
            row=2, column=0, sticky="w", padx=8, pady=10
        )
        self.txt_obtained = tk.Entry(side_box, width=18)
        self.txt_obtained.grid(row=2, column=1, padx=8, pady=10)

        tk.Label(side_box, text="Max Marks:").grid(
            row=3, column=0, sticky="w", padx=8, pady=10
        )
        self.txt_max = tk.Entry(side_box, width=18)
        self.txt_max.insert(0, "100")
        self.txt_max.grid(row=3, column=1, padx=8, pady=10)

        if self.curr_role in ("Admin", "Teacher"):
            tk.Button(
                side_box,
                text="Save Grade",
                command=self.save_grade_entry,
                bg="#4CAF50",
                fg="white",
                width=22,
            ).grid(row=4, columnspan=2, pady=20)

        data_container = tk.Frame(self.tab_ac)
        data_container.place(x=300, y=10, width=640, height=500)

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
        self.tbl_marks = self.build_grid_view(data_container, cols, heads)

        self.load_marks_data()

    def save_grade_entry(self):
        r_num = self.dd_marks_roll.get()
        subj = self.txt_subject.get().strip()
        try:
            score = float(self.txt_obtained.get().strip())
            total = float(self.txt_max.get().strip())
        except ValueError:
            messagebox.showerror("Error", "Enter valid numbers for marks.")
            return

        if total <= 0:
            messagebox.showerror("Error", "Max marks must be greater than zero.")
            return

        if score < 0 or score > total:
            messagebox.showerror(
                "Error", "Obtained marks must be between 0 and Max Marks."
            )
            return

        if not r_num or not subj:
            messagebox.showerror("Error", "Fill in all fields.")
            return

        pct = round((score / total) * 100, 2)
        letter_grade = (
            "A" if pct >= 85 else "B" if pct >= 70 else "C" if pct >= 50 else "F"
        )

        with open_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO marks (roll_no, subject, marks_obtained, max_marks, percentage, grade) VALUES (?, ?, ?, ?, ?, ?)",
                (r_num, subj, score, total, pct, letter_grade),
            )

        record_log(
            self.curr_user,
            f"Logged grade '{letter_grade}' for Roll: {r_num}, Subject: {subj}",
        )
        self.load_marks_data()
        self.txt_subject.delete(0, tk.END)
        self.txt_obtained.delete(0, tk.END)
        messagebox.showinfo("Success", "Grade recorded.")

    def load_marks_data(self):
        with open_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM marks")
            rows = cursor.fetchall()

        self.tbl_marks.delete(*self.tbl_marks.get_children())
        for r in rows:
            self.tbl_marks.insert("", "end", values=r)

    # 3. Attendance Panel
    def build_attendance_panel(self):
        side_box = tk.LabelFrame(
            self.tab_at, text="Mark Attendance", font=("Arial", 10, "bold")
        )
        side_box.place(x=10, y=10, width=280, height=500)

        tk.Label(side_box, text="Select Roll No:").grid(
            row=0, column=0, sticky="w", padx=8, pady=10
        )
        self.dd_att_roll = ttk.Combobox(side_box, width=15, state="readonly")
        self.dd_att_roll.grid(row=0, column=1, padx=8, pady=10)

        tk.Label(side_box, text="Date (YYYY-MM-DD):").grid(
            row=1, column=0, sticky="w", padx=8, pady=10
        )
        self.txt_att_date = tk.Entry(side_box, width=18)
        self.txt_att_date.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.txt_att_date.grid(row=1, column=1, padx=8, pady=10)

        tk.Label(side_box, text="Status:").grid(
            row=2, column=0, sticky="w", padx=8, pady=10
        )
        self.dd_att_status = ttk.Combobox(
            side_box,
            values=["Present", "Absent", "Late"],
            width=15,
            state="readonly",
        )
        self.dd_att_status.grid(row=2, column=1, padx=8, pady=10)

        if self.curr_role in ("Admin", "Teacher"):
            tk.Button(
                side_box,
                text="Save Attendance",
                command=self.save_attendance_entry,
                bg="#2196F3",
                fg="white",
                width=22,
            ).grid(row=3, columnspan=2, pady=20)

        data_container = tk.Frame(self.tab_at)
        data_container.place(x=300, y=10, width=640, height=500)

        cols = ("id", "roll_no", "date", "status")
        heads = ("ID", "Roll No", "Date", "Status")
        self.tbl_attendance = self.build_grid_view(data_container, cols, heads)

        self.load_attendance_data()

    def save_attendance_entry(self):
        r_num = self.dd_att_roll.get()
        d_str = self.txt_att_date.get().strip()
        st = self.dd_att_status.get()

        if not r_num or not d_str or not st:
            messagebox.showerror("Error", "All fields are required.")
            return

        with open_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO attendance (roll_no, date, status) VALUES (?, ?, ?)",
                (r_num, d_str, st),
            )

        record_log(self.curr_user, f"Marked {st} for Roll: {r_num} on {d_str}")
        self.load_attendance_data()
        messagebox.showinfo("Success", "Attendance logged.")

    def load_attendance_data(self):
        with open_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM attendance")
            rows = cursor.fetchall()

        self.tbl_attendance.delete(*self.tbl_attendance.get_children())
        for r in rows:
            self.tbl_attendance.insert("", "end", values=r)

    # 4. Analytics Panel
    def build_analytics_panel(self):
        tk.Button(
            self.tab_an,
            text="Refresh Visualizations",
            command=self.draw_charts,
            bg="#2196F3",
            fg="white",
            font=("Arial", 10, "bold"),
        ).pack(pady=10)

        self.charts_container = tk.Frame(self.tab_an)
        self.charts_container.pack(fill="both", expand=True)

        self.draw_charts()

    def draw_charts(self):
        for widget in self.charts_container.winfo_children():
            widget.destroy()

        with open_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT grade, COUNT(*) FROM marks GROUP BY grade ORDER BY grade"
            )
            g_data = dict(cursor.fetchall())

            cursor.execute(
                "SELECT status, COUNT(*) FROM attendance GROUP BY status"
            )
            a_data = dict(cursor.fetchall())

        fig = Figure(figsize=(9, 4), dpi=100)

        ax1 = fig.add_subplot(121)
        grade_keys = ["A", "B", "C", "F"]
        counts = [g_data.get(k, 0) for k in grade_keys]
        ax1.bar(
            grade_keys, counts, color=["#4CAF50", "#2196F3", "#FF9800", "#F44336"]
        )
        ax1.set_title("Grade Distribution")
        ax1.set_xlabel("Grade")
        ax1.set_ylabel("Number of Students")

        ax2 = fig.add_subplot(122)
        att_labels = list(a_data.keys()) if a_data else ["No Data"]
        att_counts = list(a_data.values()) if a_data else [1]
        ax2.pie(att_counts, labels=att_labels, autopct="%1.1f%%", startangle=90)
        ax2.set_title("Overall Attendance Spread")

        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=self.charts_container)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    # 5. Security Panel
    def build_security_panel(self):
        tk.Label(
            self.tab_sc,
            text="System Audit & Activity Logs",
            font=("Arial", 12, "bold"),
        ).pack(pady=10)

        box = tk.Frame(self.tab_sc)
        box.pack(fill="both", expand=True, padx=20, pady=10)

        cols = ("id", "username", "action", "timestamp")
        heads = ("Log ID", "User", "Action Executed", "Timestamp")
        self.tbl_logs = self.build_grid_view(box, cols, heads)

        tk.Button(
            self.tab_sc,
            text="Refresh Audit Log",
            command=self.load_audit_logs,
            bg="#9E9E9E",
            fg="white",
        ).pack(pady=10)

        self.load_audit_logs()

    def load_audit_logs(self):
        with open_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM activity_logs ORDER BY id DESC LIMIT 50"
            )
            rows = cursor.fetchall()

        self.tbl_logs.delete(*self.tbl_logs.get_children())
        for r in rows:
            self.tbl_logs.insert("", "end", values=r)

    def update_roll_lists(self):
        with open_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT roll_no FROM students")
            rolls = [r[0] for r in cursor.fetchall()]

        if hasattr(self, "dd_marks_roll"):
            self.dd_marks_roll["values"] = rolls
        if hasattr(self, "dd_att_roll"):
            self.dd_att_roll["values"] = rolls


if __name__ == "__main__":
    setup_tables()
    app_root = tk.Tk()
    LoginView(app_root)
    app_root.mainloop()
