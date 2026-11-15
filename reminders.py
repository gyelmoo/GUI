"""Reminder checks, pop-up and alert sound."""

import threading
import tkinter as tk
from datetime import date

from config import (ACCENT, CHECK_INTERVAL_MS, DARK, MUTED, TEXT, WHITE)
from helpers import alert_stage

try:                                  # Windows only; other systems fall back to bell()
    import winsound
except ImportError:
    winsound = None


class ReminderMixin:
    def stop_reminders(self):
        if self.after_id is not None:
            try:
                self.after_cancel(self.after_id)
            except tk.TclError:
                pass
            self.after_id = None

    def check_reminders(self):
        """Runs every CHECK_INTERVAL_MS while a user is logged in."""
        self.after_id = None
        if not self.user:
            return
        today = date.today()
        alerts = []
        for task in self.load_tasks():
            if task["status"] != "Pending":
                continue
            stage = alert_stage(task["due"], today)
            if stage is None:
                continue
            key = f"{today.isoformat()}:{stage}"      # one popup per task/stage/day
            if task["last_alert"] != key:
                alerts.append((task, stage))
                self.db.mark_alert(task["id"], key)

        if alerts:
            self.show_reminder_popup(alerts)
        if alerts or today != self.last_check_day:     # new day -> priorities may have changed
            self.refresh_passive_views()
        self.last_check_day = today
        self.after_id = self.after(CHECK_INTERVAL_MS, self.check_reminders)

    def describe_alert(self, task, stage):
        """Returns (label, colour, message) for one reminder."""
        plant, job = task["plant_name"], task["task_type"]
        if stage == "overdue":
            n = (date.today() - task["due"]).days
            return ("OVERDUE", "#7b1e1e",
                    f"{plant}: {job} was due {n} day{'s' if n != 1 else ''} ago. "
                    "You missed this plant care task.")
        when = "today!" if stage == "today" else "tomorrow."
        if task["priority"] == "Urgent":
            return "URGENT", "#c0392b", f"{plant}: {job} is due {when}"
        if stage == "today":
            return "DUE TODAY", "#8a6414", f"{plant}: {job} is due today."
        return "UPCOMING", "#8a6414", f"{plant}: {job} is due tomorrow."

    def show_reminder_popup(self, alerts):
        if self.popup is not None and self.popup.winfo_exists():
            self.popup.destroy()
        win = tk.Toplevel(self)
        self.popup = win
        win.title("Plant Care Reminder")
        win.configure(bg=WHITE)
        win.resizable(False, False)
        win.attributes("-topmost", True)
        win.geometry(f"+{self.winfo_rootx() + 160}+{self.winfo_rooty() + 90}")

        tk.Label(win, text="🔔  Plant Care Reminder", bg=DARK, fg=ACCENT, anchor="w",
                 font=("Helvetica", 13, "bold"), padx=18, pady=12).pack(fill="x")
        body = tk.Frame(win, bg=WHITE, padx=18, pady=8)
        body.pack(fill="both")

        severe = False
        for task, stage in alerts[:6]:
            label, colour, message = self.describe_alert(task, stage)
            severe = severe or label in ("URGENT", "OVERDUE")
            row = tk.Frame(body, bg=WHITE, pady=6)
            row.pack(fill="x")
            text_box = tk.Frame(row, bg=WHITE)
            text_box.pack(side="left", fill="x", expand=True)
            tk.Label(text_box, text=label, bg=WHITE, fg=colour,
                     font=("Helvetica", 9, "bold")).pack(anchor="w")
            tk.Label(text_box, text=message, bg=WHITE, fg=TEXT, wraplength=330,
                     justify="left", font=("Helvetica", 10)).pack(anchor="w")
            btn = tk.Button(row, text="Mark Completed", bg="#5d9d69", fg=WHITE,
                            activebackground="#4c8758", activeforeground=WHITE,
                            relief="flat", font=("Helvetica", 9, "bold"),
                            padx=10, pady=4, cursor="hand2")
            btn.config(command=lambda tid=task["id"], b=btn: self.popup_complete(tid, b))
            btn.pack(side="right", padx=(12, 0))
        if len(alerts) > 6:
            tk.Label(body, text=f"+ {len(alerts) - 6} more on your dashboard", bg=WHITE,
                     fg=MUTED, font=("Helvetica", 9)).pack(anchor="w", pady=(4, 0))

        tk.Button(win, text="Dismiss", command=win.destroy, bg=WHITE, fg=TEXT,
                  relief="solid", bd=1, padx=14, pady=4, cursor="hand2"
                  ).pack(pady=(4, 14))
        win.lift()
        self.play_alert_sound(severe)

    def popup_complete(self, task_id, button):
        next_due = self.db.complete_task(task_id)
        button.config(
            text=f"✔ Done • next {next_due}" if next_due else "✔ Done",
            state="disabled", bg="#c9d6cd"
        )
        self.refresh_passive_views()

    def play_alert_sound(self, severe):
        beeps = [(880, 180), (1175, 180), (880, 220)] if severe else [(880, 220)]
        if winsound is not None:                       # Windows
            def worker():
                for freq, ms in beeps:
                    winsound.Beep(freq, ms)
            threading.Thread(target=worker, daemon=True).start()
        else:                                          # macOS / Linux fallback
            for i in range(len(beeps)):
                self.after(i * 250, self.bell)
