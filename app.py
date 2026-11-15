"""Main window: shell, sidebar, navigation. Each page lives in its own *_view.py file."""

import tkinter as tk
from datetime import date
from tkinter import messagebox, ttk

import theme
import ui
from config import ACCENT, BG, DARK, MINT_SOFT, MUTED, SAGE, TEXT, WHITE
from database import Database
from helpers import describe_due, effective_priority, parse_date
from dashboard_view import DashboardMixin
from login_view import LoginMixin
from plant_photos import PlantPhotoMixin
from profile_view import ProfileMixin
from reminders import ReminderMixin
from search_view import SearchMixin
from summary_view import SummaryMixin
from task_form_view import TaskFormMixin

SIDEBAR_W = 250


class PlantCareApp(LoginMixin, ProfileMixin, PlantPhotoMixin, ReminderMixin, DashboardMixin,
                   TaskFormMixin, SearchMixin, SummaryMixin, tk.Tk):
    def __init__(self, db=None):
        super().__init__()
        self.title("Plant Care Scheduler")
        self.geometry("1260x780")
        self.minsize(1150, 720)
        self.configure(bg=BG)

        self.db = db or Database()
        self.user = None
        self.current_view = None
        self.editing_task_id = None
        self.after_id = None
        self.popup = None
        self.profile_win = None
        self.sidebar_avatar_holder = None
        self.search_refresh = None
        self.last_check_day = date.today()
        self.dash_filters = {"q": "", "prio": "All Priorities",
                             "status": "Pending", "plant": "All Plants"}
        self.summary_period = "All Time"

        self._set_window_icon()
        self._configure_styles()
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.show_login_screen()

    # ---------------------------------------------------------------- setup
    def _set_window_icon(self):
        img = theme.asset("logo_leaves", 64, 64)
        if img is not None:
            try:
                self.iconphoto(True, img)
            except tk.TclError:
                pass

    def _configure_styles(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(".", background=BG, font=theme.F_BODY)
        style.configure("Treeview", rowheight=34, font=(theme.UI, 10), background=WHITE,
                        fieldbackground=WHITE, foreground=TEXT, bordercolor=WHITE,
                        lightcolor=WHITE, darkcolor=WHITE, borderwidth=0)
        style.configure("Treeview.Heading", font=(theme.UI, 10, "bold"), background=MINT_SOFT,
                        foreground=DARK, relief="flat", bordercolor=MINT_SOFT,
                        lightcolor=MINT_SOFT, darkcolor=MINT_SOFT, padding=(6, 7))
        style.map("Treeview.Heading", background=[("active", "#dcebd0")])
        style.map("Treeview", background=[("selected", "#d9ead0")],
                  foreground=[("selected", TEXT)])
        style.layout("Treeview", [("Treeview.treearea", {"sticky": "nswe"})])
        style.configure("Vertical.TScrollbar", troughcolor=BG, background="#cddcc4",
                        bordercolor=BG, lightcolor="#cddcc4", darkcolor="#cddcc4",
                        arrowcolor=DARK, gripcount=0)
        style.map("Vertical.TScrollbar", background=[("active", SAGE)])
        style.configure("Green.Horizontal.TProgressbar", troughcolor="#d3e3cf",
                        background=SAGE, bordercolor="#d3e3cf",
                        lightcolor=SAGE, darkcolor=SAGE)
        ui.configure_combobox_style(self)

    def on_close(self):
        self.stop_reminders()
        self.db.close()
        self.destroy()

    def clear_root(self):
        for widget in self.winfo_children():
            widget.destroy()
        self.popup = None
        self.profile_win = None
        self.search_refresh = None

    def button(self, parent, text, command, kind="primary", icon=None, height=42,
               **pack_opts):
        """Rounded themed button. Extra keyword arguments are passed to pack()."""
        kind = {"plain": "outline"}.get(kind, kind)
        btn = ui.RoundButton(parent, text, command, kind=kind, icon=icon, height=height)
        if pack_opts:
            btn.pack(**pack_opts)
        return btn

    # ------------------------------------------------------------- sessions
    def start_session(self, user):
        self.user = user
        self.last_check_day = date.today()
        self.show_main_app("dashboard")
        self.stop_reminders()
        self.after_id = self.after(600, self.check_reminders)   # first check right after login

    # ----------------------------------------------------------- main shell
    def show_main_app(self, initial_view="dashboard"):
        self.clear_root()
        self.configure(bg=BG)

        sidebar = tk.Frame(self, bg=DARK, width=SIDEBAR_W)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        profile = tk.Frame(sidebar, bg=DARK)
        profile.pack(pady=(26, 22))
        self.sidebar_avatar_holder = tk.Frame(profile, bg=DARK)
        self.sidebar_avatar_holder.pack()
        self.build_sidebar_avatar()
        tk.Label(profile, text="Plant Care Scheduler", bg=DARK, fg=WHITE,
                 font=(theme.UI, 15, "bold")).pack(pady=(10, 2))
        edit_row = tk.Frame(profile, bg=DARK, cursor="hand2")
        edit_row.pack()
        pen = ui.icon_label(edit_row, "edit", 13, ACCENT, bg=DARK)
        pen.pack(side="left", padx=(0, 6))
        edit_text = tk.Label(edit_row, text="Edit profile photo", bg=DARK, fg="#e8f1e3",
                             font=(theme.UI, 10), cursor="hand2")
        edit_text.pack(side="left")
        for w in (edit_row, pen, edit_text):
            w.bind("<Button-1>", lambda e: self.open_profile())

        nav_items = [("Dashboard", "home", "dashboard"), ("Add Task", "plus", "add_task"),
                     ("Search", "search", "search"), ("Summary/Report", "chart", "summary")]
        self.nav_buttons = {}
        for label, icon, view_name in nav_items:
            btn = ui.RoundButton(sidebar, label, lambda n=view_name: self.nav_click(n),
                                 kind="nav", icon=icon, height=48, radius=14, align="w",
                                 padx=22, icon_size=20, font=(theme.UI, 12, "bold"), bg=DARK)
            btn.pack(fill="x", padx=16, pady=3)
            self.nav_buttons[view_name] = btn

        bottom = tk.Frame(sidebar, bg=DARK)
        bottom.pack(side="bottom", fill="x", padx=16, pady=(0, 18))
        tk.Frame(bottom, bg="#3d6b51", height=1).pack(fill="x", pady=(0, 12))
        ui.RoundButton(bottom, "Logout", self.confirm_logout, kind="nav", icon="logout",
                       height=46, radius=14, align="w", padx=22, icon_size=20,
                       font=(theme.UI, 12, "bold"), bg=DARK).pack(fill="x")

        # Flower pot in the space between the menu and Logout (sized to fit that space)
        last_nav = self.nav_buttons["summary"]
        flowers = tk.Label(sidebar, bg=DARK, bd=0)

        def place_flowers(event=None):
            try:
                top = last_nav.winfo_y() + last_nav.winfo_height() + 14
                space = bottom.winfo_y() - 14 - top
            except tk.TclError:
                return
            if space < 70:                       # window too short: leave it out
                flowers.place_forget()
                return
            img = theme.asset("sidebar_flowers", SIDEBAR_W - 50, min(space, 240))
            if img is None:
                return
            flowers.config(image=img)
            flowers.image = img
            flowers.place(x=SIDEBAR_W // 2, y=top + space // 2, anchor="center")

        sidebar.bind("<Configure>", place_flowers)
        self.after(80, place_flowers)
        self.after(400, place_flowers)      # again once the window has its final size

        self.content_area = tk.Frame(self, bg=BG, padx=26, pady=12)
        self.content_area.pack(side="right", expand=True, fill="both")
        self.switch_view(initial_view)

    def nav_click(self, view_name):
        self.editing_task_id = None          # sidebar "Add Task" always opens a blank form
        self.switch_view(view_name)

    def switch_view(self, view_name):
        self.current_view = view_name
        self.search_refresh = None
        for name, btn in self.nav_buttons.items():
            btn.set_kind("nav_active" if name == view_name else "nav")
        for child in self.content_area.winfo_children():
            child.destroy()
        getattr(self, f"render_{view_name}")()

    def refresh_passive_views(self):
        """Re-draw dashboard/summary (never the form, so nothing typed is lost).

        The Search page keeps what was typed and simply runs the search again.
        """
        if not self.user:
            return
        if self.current_view in ("dashboard", "summary"):
            self.switch_view(self.current_view)
        elif self.current_view == "search" and self.search_refresh is not None:
            self.search_refresh()

    def confirm_logout(self):
        if messagebox.askyesno("Confirm Logout", "Are you sure you want to logout?"):
            self.show_login_screen()

    def page_header(self, title, subtitle, icon="leaf", plant="hanging_pothos"):
        """Icon + title + subtitle on the left, a hanging plant on the right."""
        header = ui.PageHeader(self.content_area, title, subtitle, icon=icon, plant=plant)
        header.pack(fill="x", pady=(0, 8))
        return header

    # ------------------------------------------------------------ data access
    def load_tasks(self):
        today = date.today()
        tasks = []
        for row in self.db.fetch_tasks(self.user["id"]):
            row["due"] = parse_date(row["due_date"])
            row["priority"] = effective_priority(row["base_priority"], row["status"],
                                                 row["due"], today)
            row["due_in"] = (describe_due(row["due"], today)
                             if row["status"] == "Pending" else "")
            tasks.append(row)
        return tasks