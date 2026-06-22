# =============================================================================
# PROG103 - PRINCIPLE OF STRUCTURED PROGRAMMING
# FINAL PROJECT - BBIT1101F - GROUP 8
# Limkokwing University of Creative Technology, Sierra Leone
#
# Project Title : Community Health Clinic Queue Management System
# SDG Alignment : SDG 3 – Good Health and Well-Being
# Description   : A GUI-based queue management system designed to improve
#                 patient service delivery in Sierra Leone's public clinics.
# License       : MIT License
# GitHub Repo   : PROG103_FinalProject_BBIT1101F_Group8
# =============================================================================

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import json
import os

# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────
APP_TITLE       = "Community Health Clinic Queue System"
CLINIC_NAME     = "Freetown Community Health Centre"
PRIORITY_LEVELS = ["Normal", "Urgent", "Emergency"]
DEPARTMENTS     = ["General OPD", "Maternity", "Paediatrics", "Pharmacy", "Laboratory"]
DATA_FILE       = os.path.join(os.path.dirname(os.path.abspath(__file__)), "clinic_data.json")

# Colour palette (clean, professional)
BG_MAIN     = "#F0F4F8"
BG_HEADER   = "#1A6B3A"   # deep green (SDG 3 colour)
BG_CARD     = "#FFFFFF"
FG_HEADER   = "#FFFFFF"
FG_DARK     = "#1A1A2E"
FG_MUTED    = "#6B7280"
ACCENT      = "#22863A"
ACCENT_WARN = "#D97706"
ACCENT_EMRG = "#DC2626"
BTN_CLEAR   = "#6B7280"

# ─────────────────────────────────────────────────────────────────────────────
# BUSINESS LOGIC FUNCTIONS (separated from GUI)
# ─────────────────────────────────────────────────────────────────────────────

def generate_ticket_number(counter: int) -> str:
    """Generate a zero-padded ticket number string."""
    return f"TKT-{counter:04d}"


def determine_priority_colour(priority: str) -> str:
    """Return a display colour based on triage priority level."""
    if priority == "Emergency":
        return ACCENT_EMRG
    elif priority == "Urgent":
        return ACCENT_WARN
    else:
        return ACCENT


def calculate_estimated_wait(queue: list, priority: str) -> int:
    """
    Estimate waiting time in minutes.
    Emergency: 5 min per person ahead who is also emergency, else 2 min.
    Urgent: 7 min per normal patient ahead, 10 min per urgent.
    Normal: 10 min per patient ahead.
    """
    wait = 0
    for patient in queue:
        p = patient["priority"]
        if priority == "Emergency":
            wait += 5 if p == "Emergency" else 2
        elif priority == "Urgent":
            wait += 10 if p in ("Emergency", "Urgent") else 7
        else:
            wait += 10
    return wait


def validate_patient_input(name: str, age_str: str, department: str) -> tuple:
    """
    Validate user input fields.
    Returns (is_valid: bool, message: str).
    """
    name = name.strip()
    if not name:
        return False, "Patient name cannot be empty."
    if len(name) < 2:
        return False, "Patient name must be at least 2 characters."
    if not name.replace(" ", "").isalpha():
        return False, "Patient name must contain letters only."

    if not age_str.strip().isdigit():
        return False, "Age must be a whole number."
    age = int(age_str.strip())
    if age < 0 or age > 120:
        return False, "Age must be between 0 and 120."

    if not department:
        return False, "Please select a department."

    return True, "OK"


def sort_queue_by_priority(queue: list) -> list:
    """
    Sort the queue: Emergency first, then Urgent, then Normal.
    Within the same priority, order by registration time (FIFO).
    """
    priority_order = {"Emergency": 0, "Urgent": 1, "Normal": 2}
    return sorted(queue, key=lambda p: priority_order[p["priority"]])


def search_patient(queue: list, keyword: str) -> list:
    """Search patients in the queue by name or ticket number (case-insensitive)."""
    keyword = keyword.lower().strip()
    results = []
    for patient in queue:
        if keyword in patient["name"].lower() or keyword in patient["ticket"].lower():
            results.append(patient)
    return results


def generate_statistics(queue: list, served: list) -> dict:
    """Calculate summary statistics for the dashboard."""
    total_waiting   = len(queue)
    total_served    = len(served)
    emergency_count = sum(1 for p in queue if p["priority"] == "Emergency")
    urgent_count    = sum(1 for p in queue if p["priority"] == "Urgent")
    normal_count    = sum(1 for p in queue if p["priority"] == "Normal")
    dept_counts = {}
    for p in queue + served:
        dept = p["department"]
        dept_counts[dept] = dept_counts.get(dept, 0) + 1
    return {
        "waiting":   total_waiting,
        "served":    total_served,
        "emergency": emergency_count,
        "urgent":    urgent_count,
        "normal":    normal_count,
        "by_dept":   dept_counts,
    }


def save_clinic_data(queue: list, served: list, ticket_counter: int):
    """Save the queue, served list, and ticket counter to a JSON file."""
    try:
        data = {
            "queue":          queue,
            "served":         served,
            "ticket_counter": ticket_counter
        }
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Warning: Could not save data — {e}")


def load_clinic_data() -> tuple:
    """
    Load the queue, served list, and ticket counter from the JSON file.
    Returns (queue: list, served: list, ticket_counter: int).
    If no saved file exists yet, returns empty defaults.
    """
    if not os.path.exists(DATA_FILE):
        return [], [], 1
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        queue          = data.get("queue", [])
        served         = data.get("served", [])
        ticket_counter = data.get("ticket_counter", 1)
        return queue, served, ticket_counter
    except Exception as e:
        print(f"Warning: Could not load data — {e}")
        return [], [], 1


# ─────────────────────────────────────────────────────────────────────────────
# GUI APPLICATION CLASS
# ─────────────────────────────────────────────────────────────────────────────

class ClinicQueueApp:
    """
    Main application class for the Community Health Clinic Queue System.
    Implements structured programming principles:
      - Modular functions
      - Decision structures (if/elif/else)
      - Iteration (loops over queue and served lists)
      - Variables & constants
      - Data types (str, int, list, dict, bool)
    """

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("1100x720")
        self.root.resizable(True, True)
        self.root.configure(bg=BG_MAIN)

        # Application state — restored from saved file if available
        self.queue, self.served, self.ticket_counter = load_clinic_data()

        self._build_ui()
        self._refresh_queue_display()
        self._refresh_stats()

    # ── UI CONSTRUCTION ──────────────────────────────────────────────────────

    def _build_ui(self):
        """Build the complete user interface layout."""
        self._build_header()
        self._build_main_area()
        self._build_footer()

    def _build_header(self):
        """Build the top header bar."""
        header = tk.Frame(self.root, bg=BG_HEADER, height=70)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(
            header, text=f"🏥  {CLINIC_NAME}",
            bg=BG_HEADER, fg=FG_HEADER,
            font=("Tahoma", 16, "bold")
        ).pack(side="left", padx=20, pady=15)

        tk.Label(
            header, text=APP_TITLE,
            bg=BG_HEADER, fg="#A7F3D0",
            font=("Tahoma", 11)
        ).pack(side="left", padx=5, pady=15)

        self.lbl_time = tk.Label(
            header, text="", bg=BG_HEADER, fg=FG_HEADER,
            font=("Tahoma", 10)
        )
        self.lbl_time.pack(side="right", padx=20)
        self._update_clock()

    def _update_clock(self):
        """Refresh the live clock in the header every second."""
        now = datetime.now().strftime("%A, %d %B %Y  |  %H:%M:%S")
        self.lbl_time.config(text=now)
        self.root.after(1000, self._update_clock)

    def _build_main_area(self):
        """Build the two-column main content area."""
        main = tk.Frame(self.root, bg=BG_MAIN)
        main.pack(fill="both", expand=True, padx=15, pady=10)

        # Left panel – registration + stats
        left = tk.Frame(main, bg=BG_MAIN, width=360)
        left.pack(side="left", fill="y", padx=(0, 10))
        left.pack_propagate(False)

        self._build_registration_panel(left)
        self._build_stats_panel(left)

        # Right panel – queue display
        right = tk.Frame(main, bg=BG_MAIN)
        right.pack(side="left", fill="both", expand=True)

        self._build_queue_panel(right)

    def _build_registration_panel(self, parent):
        """Build the patient registration form."""
        card = self._make_card(parent, "Patient Registration")

        # Name
        self._make_label(card, "Full Name *")
        self.entry_name = self._make_entry(card)

        # Age
        self._make_label(card, "Age *")
        self.entry_age = self._make_entry(card)

        # Gender
        self._make_label(card, "Gender")
        self.var_gender = tk.StringVar(value="Male")
        gf = tk.Frame(card, bg=BG_CARD)
        gf.pack(fill="x", pady=(0, 8))
        for g in ("Male", "Female", "Other"):
            tk.Radiobutton(
                gf, text=g, variable=self.var_gender, value=g,
                bg=BG_CARD, fg=FG_DARK, font=("Tahoma", 10),
                activebackground=BG_CARD
            ).pack(side="left", padx=4)

        # Department
        self._make_label(card, "Department *")
        self.combo_dept = ttk.Combobox(
            card, values=DEPARTMENTS, state="readonly", font=("Tahoma", 10)
        )
        self.combo_dept.pack(fill="x", pady=(0, 8))

        # Priority
        self._make_label(card, "Triage Priority *")
        self.var_priority = tk.StringVar(value="Normal")
        pf = tk.Frame(card, bg=BG_CARD)
        pf.pack(fill="x", pady=(0, 10))
        colours = {"Normal": ACCENT, "Urgent": ACCENT_WARN, "Emergency": ACCENT_EMRG}
        for lvl in PRIORITY_LEVELS:
            tk.Radiobutton(
                pf, text=lvl, variable=self.var_priority, value=lvl,
                bg=BG_CARD, fg=colours[lvl], font=("Tahoma", 10, "bold"),
                activebackground=BG_CARD
            ).pack(side="left", padx=4)

        # Buttons
        bf = tk.Frame(card, bg=BG_CARD)
        bf.pack(fill="x", pady=(5, 0))

        tk.Button(
            bf, text="✔  Register Patient",
            bg=ACCENT, fg="white", font=("Tahoma", 10, "bold"),
            relief="flat", cursor="hand2", padx=10, pady=6,
            command=self._register_patient
        ).pack(side="left", expand=True, fill="x", padx=(0, 5))

        tk.Button(
            bf, text="✖  Clear",
            bg=BTN_CLEAR, fg="white", font=("Tahoma", 10),
            relief="flat", cursor="hand2", padx=10, pady=6,
            command=self._clear_form
        ).pack(side="left")

    def _build_stats_panel(self, parent):
        """Build the live statistics dashboard."""
        card = self._make_card(parent, "Live Statistics")

        self.stat_vars = {}
        stats_def = [
            ("waiting",   "⏳ Waiting",    FG_DARK),
            ("served",    "✅ Served",      ACCENT),
            ("emergency", "🔴 Emergency",   ACCENT_EMRG),
            ("urgent",    "🟠 Urgent",      ACCENT_WARN),
            ("normal",    "🟢 Normal",      ACCENT),
        ]
        for key, label, colour in stats_def:
            row = tk.Frame(card, bg=BG_CARD)
            row.pack(fill="x", pady=2)
            tk.Label(row, text=label, bg=BG_CARD, fg=FG_MUTED,
                     font=("Tahoma", 10)).pack(side="left")
            var = tk.StringVar(value="0")
            self.stat_vars[key] = var
            tk.Label(row, textvariable=var, bg=BG_CARD, fg=colour,
                     font=("Tahoma", 12, "bold")).pack(side="right")

    def _build_queue_panel(self, parent):
        """Build the queue table and action buttons."""
        # Search bar
        search_frame = tk.Frame(parent, bg=BG_MAIN)
        search_frame.pack(fill="x", pady=(0, 8))

        tk.Label(search_frame, text="🔍 Search:", bg=BG_MAIN,
                 fg=FG_DARK, font=("Tahoma", 10)).pack(side="left")
        self.entry_search = tk.Entry(search_frame, font=("Tahoma", 10), width=25)
        self.entry_search.pack(side="left", padx=6)
        tk.Button(
            search_frame, text="Search", bg=ACCENT, fg="white",
            font=("Tahoma", 9), relief="flat", cursor="hand2",
            command=self._search_queue
        ).pack(side="left")
        tk.Button(
            search_frame, text="Show All", bg=BTN_CLEAR, fg="white",
            font=("Tahoma", 9), relief="flat", cursor="hand2",
            command=self._refresh_queue_display
        ).pack(side="left", padx=4)

        # Queue tabs
        notebook = ttk.Notebook(parent)
        notebook.pack(fill="both", expand=True)

        self.tab_queue  = ttk.Frame(notebook)
        self.tab_served = ttk.Frame(notebook)
        notebook.add(self.tab_queue,  text="  Current Queue  ")
        notebook.add(self.tab_served, text="  Served Patients  ")

        self.tree_queue  = self._build_tree(self.tab_queue)
        self.tree_served = self._build_tree(self.tab_served, served=True)

        # Action buttons
        af = tk.Frame(parent, bg=BG_MAIN)
        af.pack(fill="x", pady=(8, 0))

        tk.Button(
            af, text="✅  Call Next Patient",
            bg=ACCENT, fg="white", font=("Tahoma", 10, "bold"),
            relief="flat", cursor="hand2", padx=12, pady=6,
            command=self._call_next_patient
        ).pack(side="left", padx=(0, 8))

        tk.Button(
            af, text="🗑  Remove Selected",
            bg=ACCENT_EMRG, fg="white", font=("Tahoma", 10),
            relief="flat", cursor="hand2", padx=12, pady=6,
            command=self._remove_selected
        ).pack(side="left", padx=(0, 8))

        tk.Button(
            af, text="🔄  Refresh",
            bg=BTN_CLEAR, fg="white", font=("Tahoma", 10),
            relief="flat", cursor="hand2", padx=12, pady=6,
            command=self._refresh_queue_display
        ).pack(side="left")

    def _build_tree(self, parent, served=False) -> ttk.Treeview:
        """Build a Treeview table widget for queue or served patients."""
        cols = ("ticket", "name", "age", "gender", "department", "priority", "time", "wait")
        headings = ("Ticket", "Full Name", "Age", "Gender", "Department",
                    "Priority", "Registered", "Est. Wait (min)")

        frame = tk.Frame(parent, bg=BG_CARD)
        frame.pack(fill="both", expand=True, padx=2, pady=2)

        tree = ttk.Treeview(frame, columns=cols, show="headings", height=16)

        col_widths = [80, 140, 45, 60, 110, 90, 90, 100]
        for col, heading, width in zip(cols, headings, col_widths):
            tree.heading(col, text=heading)
            tree.column(col, width=width, anchor="center")

        # Scrollbars
        vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        hsb = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)

        # Priority row tags for colour coding
        tree.tag_configure("Emergency", foreground=ACCENT_EMRG, font=("Tahoma", 9, "bold"))
        tree.tag_configure("Urgent",    foreground=ACCENT_WARN, font=("Tahoma", 9, "bold"))
        tree.tag_configure("Normal",    foreground=FG_DARK,     font=("Tahoma", 9))

        style = ttk.Style()
        style.configure("Treeview.Heading", font=("Tahoma", 9, "bold"),
                        background="#E5E7EB", foreground=FG_DARK)
        style.configure("Treeview", rowheight=26, font=("Tahoma", 9))

        return tree

    def _build_footer(self):
        """Build the status bar at the bottom."""
        footer = tk.Frame(self.root, bg=BG_HEADER, height=28)
        footer.pack(fill="x", side="bottom")
        footer.pack_propagate(False)

        self.lbl_status = tk.Label(
            footer,
            text="System ready.  SDG 3 – Good Health and Well-Being  |  MIT License  |  Group 8",
            bg=BG_HEADER, fg="#A7F3D0", font=("Tahoma", 9)
        )
        self.lbl_status.pack(side="left", padx=12, pady=5)

        tk.Button(
            footer, text="Exit System",
            bg="#991B1B", fg="white", font=("Tahoma", 9),
            relief="flat", cursor="hand2",
            command=self._exit_app
        ).pack(side="right", padx=10, pady=3)

    # ── HELPER UI BUILDERS ───────────────────────────────────────────────────

    def _make_card(self, parent, title: str) -> tk.Frame:
        """Create a white card container with a bold title."""
        outer = tk.Frame(parent, bg=BG_MAIN)
        outer.pack(fill="x", pady=(0, 10))

        tk.Label(outer, text=title.upper(), bg=BG_MAIN,
                 fg=BG_HEADER, font=("Tahoma", 10, "bold")).pack(anchor="w", pady=(0, 4))

        inner = tk.Frame(outer, bg=BG_CARD, bd=1, relief="groove")
        inner.pack(fill="x")

        content = tk.Frame(inner, bg=BG_CARD, padx=14, pady=10)
        content.pack(fill="x")
        return content

    def _make_label(self, parent, text: str):
        tk.Label(parent, text=text, bg=BG_CARD, fg=FG_MUTED,
                 font=("Tahoma", 9)).pack(anchor="w")

    def _make_entry(self, parent) -> tk.Entry:
        e = tk.Entry(parent, font=("Tahoma", 10), bd=1, relief="solid")
        e.pack(fill="x", pady=(2, 8), ipady=4)
        return e

    # ── APPLICATION LOGIC FUNCTIONS ──────────────────────────────────────────

    def _register_patient(self):
        """Collect form input, validate, create patient record, add to queue."""
        name       = self.entry_name.get()
        age_str    = self.entry_age.get()
        gender     = self.var_gender.get()
        department = self.combo_dept.get()
        priority   = self.var_priority.get()

        # Validate using business logic function
        valid, message = validate_patient_input(name, age_str, department)
        if not valid:
            messagebox.showerror("Validation Error", message)
            return

        # Build patient record (dictionary)
        ticket = generate_ticket_number(self.ticket_counter)
        self.ticket_counter += 1

        patient = {
            "ticket":     ticket,
            "name":       name.strip().title(),
            "age":        int(age_str.strip()),
            "gender":     gender,
            "department": department,
            "priority":   priority,
            "time":       datetime.now().strftime("%H:%M:%S"),
        }

        self.queue.append(patient)
        self.queue = sort_queue_by_priority(self.queue)

        wait = calculate_estimated_wait(
            [p for p in self.queue if p["ticket"] != ticket], priority
        )
        patient["wait"] = wait

        self._refresh_queue_display()
        self._refresh_stats()
        self._clear_form()
        self._save_data()

        colour = determine_priority_colour(priority)
        msg = (f"Patient registered successfully!\n\n"
               f"Ticket  : {ticket}\n"
               f"Name    : {patient['name']}\n"
               f"Priority: {priority}\n"
               f"Dept    : {department}\n"
               f"Est. Wait: ~{wait} min")
        messagebox.showinfo("Registration Successful", msg)
        self._set_status(f"Registered: {patient['name']}  [{ticket}]  Priority: {priority}")

    def _call_next_patient(self):
        """Remove the top-priority patient from the queue and mark as served."""
        if not self.queue:
            messagebox.showinfo("Empty Queue", "No patients currently in the queue.")
            return

        # The queue is already sorted; take the first patient
        patient = self.queue.pop(0)
        patient["served_at"] = datetime.now().strftime("%H:%M:%S")
        self.served.append(patient)

        self._refresh_queue_display()
        self._refresh_stats()
        self._save_data()

        msg = (f"Calling patient:\n\n"
               f"Ticket  : {patient['ticket']}\n"
               f"Name    : {patient['name']}\n"
               f"Priority: {patient['priority']}\n"
               f"Dept    : {patient['department']}")
        messagebox.showinfo("Next Patient", msg)
        self._set_status(f"Now serving: {patient['name']}  [{patient['ticket']}]")

    def _remove_selected(self):
        """Remove a selected patient record from the queue."""
        selected = self.tree_queue.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a patient from the queue.")
            return

        item   = selected[0]
        values = self.tree_queue.item(item, "values")
        ticket = values[0]

        confirm = messagebox.askyesno(
            "Confirm Removal",
            f"Remove ticket {ticket} – {values[1]} from the queue?"
        )
        if not confirm:
            return

        # Find and remove from queue list using a loop
        for i, patient in enumerate(self.queue):
            if patient["ticket"] == ticket:
                self.queue.pop(i)
                break

        self._refresh_queue_display()
        self._refresh_stats()
        self._save_data()
        self._set_status(f"Removed patient: {values[1]}  [{ticket}]")

    def _search_queue(self):
        """Filter queue display by search keyword."""
        keyword = self.entry_search.get()
        if not keyword.strip():
            self._refresh_queue_display()
            return

        results = search_patient(self.queue, keyword)
        self._populate_tree(self.tree_queue, results)
        self._set_status(f"Search results for '{keyword}': {len(results)} found.")

    def _clear_form(self):
        """Reset all registration form fields to defaults."""
        self.entry_name.delete(0, tk.END)
        self.entry_age.delete(0, tk.END)
        self.var_gender.set("Male")
        self.combo_dept.set("")
        self.var_priority.set("Normal")
        self.entry_name.focus()

    def _refresh_queue_display(self):
        """Repopulate both treeviews from current state lists."""
        self._populate_tree(self.tree_queue,  self.queue)
        self._populate_tree(self.tree_served, self.served)

    def _populate_tree(self, tree: ttk.Treeview, data: list):
        """Clear a Treeview and insert new rows from a list of patient dicts."""
        for row in tree.get_children():
            tree.delete(row)

        for patient in data:
            wait_display = f"~{patient.get('wait', 0)}"
            values = (
                patient["ticket"],
                patient["name"],
                patient["age"],
                patient["gender"],
                patient["department"],
                patient["priority"],
                patient["time"],
                wait_display,
            )
            tree.insert("", tk.END, values=values, tags=(patient["priority"],))

    def _refresh_stats(self):
        """Recalculate and update all statistics labels."""
        stats = generate_statistics(self.queue, self.served)
        for key, var in self.stat_vars.items():
            var.set(str(stats.get(key, 0)))

    def _set_status(self, message: str):
        """Update the footer status bar text."""
        self.lbl_status.config(text=f"  {message}")

    def _save_data(self):
        """Persist the current queue, served list, and ticket counter to disk."""
        save_clinic_data(self.queue, self.served, self.ticket_counter)

    def _exit_app(self):
        """Prompt confirmation, save data, and exit the application."""
        confirm = messagebox.askyesno(
            "Exit System",
            "Are you sure you want to exit the Clinic Queue System?"
        )
        if confirm:
            self._save_data()
            self.root.destroy()


# ─────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────


# ─────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

def main():
    """Application entry point."""
    root = tk.Tk()
    app = ClinicQueueApp(root)
    # Ensure data is saved if the user closes the window using the X button,
    # not only when using the in-app Exit System button.
    root.protocol("WM_DELETE_WINDOW", lambda: (app._save_data(), root.destroy()))
    root.mainloop()


if __name__ == "__main__":
    main()