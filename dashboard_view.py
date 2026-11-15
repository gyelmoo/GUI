"""Home dashboard."""

import os
import tkinter as tk
from datetime import date, datetime
from tkinter import messagebox

import theme
import ui
from config import (BAD, BG, BORDER, DARK, MAX_SEARCH, MINT_SOFT, MUTED, PILL, PINK_SOFT,
                    SAGE, SAGE_LIGHT, TEXT, WHITE, YELLOW_SOFT)
from helpers import describe_due
from widgets import ScrollFrame, limit_entry

PLANT_TIPS = [
    "Water your plants when the topsoil feels dry to the touch.",
    "Keep the soil moist, not soggy - soggy roots can rot.",
    "Turn your pots a little every week so plants grow evenly.",
    "Wipe dusty leaves with a damp cloth so they can breathe and catch light.",
    "Most houseplants love bright light, but not harsh afternoon sun.",
    "Feed plants during the growing season; rest them in winter.",
    "Yellow lower leaves often mean too much water.",
]


def plant_tip(day=None):
    day = day or date.today()
    return PLANT_TIPS[day.toordinal() % len(PLANT_TIPS)]


class DashboardMixin:
    def render_dashboard(self):
        tasks = self.load_tasks()
        pending = [t for t in tasks if t["status"] == "Pending"]
        total, done = len(tasks), len(tasks) - len(pending)
        pct = int(done / total * 100) if total else 0
        overdue_n = sum(1 for t in pending if t["priority"] == "Overdue")
        upcoming_n = len(pending) - overdue_n
        attention = sum(1 for t in pending if t["priority"] in ("Urgent", "Overdue"))
        plants_n = len({t["plant_id"] for t in tasks})

        hour = datetime.now().hour
        greeting = "morning" if hour < 12 else "afternoon" if hour < 17 else "evening"
        name = self.user["username"].title()

        # ---------------------------------------------------------- header
        if attention:
            subtitle = f"{attention} task{'s' if attention != 1 else ''} need your attention."
            sub_colour = BAD
        else:
            subtitle, sub_colour = "Healthy plants, happier days", TEXT
        header = ui.PageHeader(self.content_area, f"Good {greeting}, {name}!", subtitle,
                               show_badge=False, title_font=theme.F_GREETING,
                               subtitle_font=theme.F_SUBTITLE, subtitle_colour=sub_colour,
                               plant="hanging_basket")
        header.pack(fill="x", pady=(0, 6))

        controls = header.controls
        chip = ui.RoundBox(controls, fill=WHITE, radius=20, border=BORDER, padx=14, pady=7,
                           shadow=3)
        chip.pack(side="left", padx=(0, 10))
        ui.icon_label(chip.inner, "calendar", 18, DARK, bg=WHITE).pack(side="left", padx=(0, 8))
        tk.Label(chip.inner, text=date.today().strftime("%a, %d %b %Y"), bg=WHITE, fg=TEXT,
                 font=(theme.UI, 10, "bold")).pack(side="left")
        ui.IconButton(controls, "bell", lambda: self.show_bell_summary(attention, overdue_n,
                                                                       upcoming_n),
                      colour=DARK, fill=WHITE, hover=SAGE_LIGHT, size=38, icon_size=18
                      ).pack(side="left", padx=(0, 10))
        ui.RoundButton(controls, "Add Task", lambda: self.nav_click("add_task"), icon="plus",
                       height=44, radius=22, font=(theme.UI, 11, "bold")).pack(side="left")

        # ------------------------------------------------------ stat cards
        stats = tk.Frame(self.content_area, bg=BG)
        stats.pack(fill="x", pady=(0, 12))
        cards = [
            ("Total Plants", plants_n, PINK_SOFT, ("asset", "monstera_pot", "#f9d0d0")),
            ("Total Tasks", total, MINT_SOFT, ("icon", "clipboard", "#cfe4c4", DARK)),
            ("Upcoming", upcoming_n, YELLOW_SOFT, ("icon", "clock", "#f8dc9c", "#8a5a12")),
            ("Overdue", overdue_n, "#fde3e1", ("asset", "icon_alert", None)),
        ]
        for i, (label, value, fill, art) in enumerate(cards):
            box = ui.RoundBox(stats, fill=fill, radius=18, shadow=5, padx=18, pady=14)
            box.grid(row=0, column=i, sticky="nsew", padx=(0 if i == 0 else 7, 0))
            stats.columnconfigure(i, weight=1, uniform="stat")
            self._stat_art(box.inner, art, fill).pack(side="left", padx=(0, 14))
            text_box = tk.Frame(box.inner, bg=fill)
            text_box.pack(side="left")
            tk.Label(text_box, text=str(value), bg=fill, fg=TEXT,
                     font=theme.F_STAT).pack(anchor="w")
            tk.Label(text_box, text=label, bg=fill, fg=TEXT,
                     font=(theme.UI, 11)).pack(anchor="w")

        # ----------------------------------------------------------- body
        body = tk.Frame(self.content_area, bg=BG)
        body.pack(fill="both", expand=True)
        body.columnconfigure(0, weight=1)
        body.rowconfigure(1, weight=1)

        # filter bar
        filters = self.dash_filters
        plant_names = sorted({t["plant_name"] for t in tasks})
        if filters["plant"] not in ["All Plants"] + plant_names:
            filters["plant"] = "All Plants"
        search_var = tk.StringVar(value=filters["q"])
        prio_var = tk.StringVar(value=filters["prio"])
        status_var = tk.StringVar(value=filters["status"])
        plant_var = tk.StringVar(value=filters["plant"])

        bar = tk.Frame(body, bg=BG)
        bar.grid(row=0, column=0, sticky="ew", pady=(0, 10), padx=(0, 14))
        search_field, search_entry = ui.entry_field(bar, icon="search", icon_colour=MUTED,
                                                    placeholder="Search plants or tasks...",
                                                    textvariable=search_var,
                                                    font=(theme.UI, 10))
        search_field.pack(side="left", fill="x", expand=True, padx=(0, 8))
        limit_entry(search_entry, MAX_SEARCH)
        for values, var, width in (
                (["All Priorities", "Urgent", "Overdue", "Routine", "Optional"], prio_var, 12),
                (["All Statuses", "Pending", "Completed"], status_var, 11),
                (["All Plants"] + plant_names, plant_var, 12)):
            field, _ = ui.combo_field(bar, values, width=width, textvariable=var,
                                      font=(theme.UI, 10))
            field.pack(side="left", padx=(0, 6))

        # task list card
        list_card = ui.card(body, fit=False, padx=18, pady=14)
        list_card.grid(row=1, column=0, sticky="nsew", padx=(0, 14))
        head = tk.Frame(list_card.inner, bg=WHITE)
        head.pack(fill="x", pady=(0, 8))
        title_row = ui.section_title(head, "Upcoming Tasks", "sprout", bg=WHITE)
        title_row.pack(side="left")
        list_title = title_row.winfo_children()[-1]
        count_label = tk.Label(head, text="", bg=WHITE, fg=MUTED, font=(theme.UI, 10))
        count_label.pack(side="right")
        tk.Frame(list_card.inner, bg="#efeadb", height=1).pack(fill="x", pady=(0, 6))
        scroller = ScrollFrame(list_card.inner, bg=WHITE)
        scroller.pack(fill="both", expand=True)

        # right-hand tip / progress card
        tip = ui.RoundBox(body, fill=MINT_SOFT, radius=20, shadow=5, padx=18, pady=16,
                          fit=False, width=240)
        tip.grid(row=0, column=1, rowspan=2, sticky="ns")
        self._tip_card(tip.inner, MINT_SOFT, pct, done, total)

        def populate(*_):
            filters.update(q=search_var.get(), prio=prio_var.get(),
                           status=status_var.get(), plant=plant_var.get())
            q = search_var.get().strip().lower()

            def matches(t):
                if q and not (q in t["plant_id"].lower() or q in t["plant_name"].lower()
                              or q in t["task_type"].lower() or q in t["priority"].lower()
                              or q in t["notes"].lower()):
                    return False
                if prio_var.get() != "All Priorities" and t["priority"] != prio_var.get():
                    return False
                if status_var.get() != "All Statuses" and t["status"] != status_var.get():
                    return False
                if plant_var.get() != "All Plants" and t["plant_name"] != plant_var.get():
                    return False
                return True

            rows = [t for t in tasks if matches(t)]
            rows.sort(key=lambda t: (t["status"] != "Pending", t["due"], t["id"]))

            list_title.config(text={"Pending": "Upcoming Tasks",
                                    "Completed": "Completed Tasks"
                                    }.get(status_var.get(), "All Tasks"))
            count_label.config(text=f"{len(rows)} task{'s' if len(rows) != 1 else ''}")

            for child in scroller.inner.winfo_children():
                child.destroy()
            scroller.canvas.yview_moveto(0)
            if not rows:
                self._empty_state(scroller.inner, bool(tasks),
                                  lambda: (search_var.set(""), prio_var.set("All Priorities"),
                                           status_var.set("All Statuses"),
                                           plant_var.set("All Plants")))
                return
            for t in rows:
                self._task_row(scroller.inner, t)

        search_var.trace_add("write", populate)
        for var in (prio_var, status_var, plant_var):
            var.trace_add("write", populate)
        populate()

    # ------------------------------------------------------------- pieces
    def _stat_art(self, parent, art, bg):
        size = 58
        if art[0] == "icon":
            _, name, circle, colour = art
            return ui.badge_label(parent, name, size, circle, colour, bg=bg, scale=0.5)
        _, name, circle = art
        lbl = tk.Label(parent, bg=bg, bd=0)
        img = None
        if theme.PIL_OK:
            key = ("statart", name, circle, size)
            img = theme._cache.get(key)
            if img is None:
                from PIL import Image, ImageDraw
                base = Image.new("RGBA", (size * 3, size * 3), (0, 0, 0, 0))
                if circle:
                    ImageDraw.Draw(base).ellipse((0, 0, size * 3 - 1, size * 3 - 1),
                                                 fill=theme.hex_rgb(circle))
                base = base.resize((size, size), Image.LANCZOS)
                inner = int(size * (0.74 if circle else 1.0))
                pic = theme.asset_pil(name, inner, inner)
                base.alpha_composite(pic, ((size - pic.width) // 2, (size - pic.height) // 2))
                img = theme.photo(base)
                theme._cache[key] = img
        if img is not None:
            lbl.config(image=img)
            lbl.image = img
        return lbl

    def _tip_card(self, parent, bg, pct, done, total):
        top = tk.Frame(parent, bg=bg)
        top.pack(fill="x", pady=(6, 0))
        ui.icon_label(top, "bulb", 30, DARK, bg=bg).pack(side="left", padx=(4, 10))
        tk.Label(top, text="Plant Care Tip", bg=bg, fg=DARK,
                 font=(theme.UI, 14, "bold")).pack(side="left")
        tk.Label(parent, text=plant_tip(), bg=bg, fg=TEXT, wraplength=195, justify="center",
                 font=(theme.UI, 11)).pack(pady=(14, 6))
        sprig = theme.deco_label(parent, "sprig_small", 26, 26, bg=bg)
        sprig.pack()

        progress = tk.Frame(parent, bg=bg)
        progress.pack(fill="x", pady=(14, 0))
        row = tk.Frame(progress, bg=bg)
        row.pack(fill="x")
        tk.Label(row, text="Your progress", bg=bg, fg=DARK,
                 font=(theme.UI, 10, "bold")).pack(side="left")
        tk.Label(row, text=f"{pct}%", bg=bg, fg=DARK,
                 font=(theme.UI, 10, "bold")).pack(side="right")
        ui.RoundProgress(progress, value=pct, height=12, track="#d3e5c8", bg=bg
                         ).pack(fill="x", pady=(6, 4))
        tk.Label(progress, text=f"{done} of {total} tasks completed", bg=bg, fg=MUTED,
                 font=theme.F_SMALL).pack(anchor="w")

        theme.deco_label(parent, "cute_pot", 150, 140, bg=bg).pack(side="bottom", pady=(0, 2))

    def _empty_state(self, parent, has_tasks, clear_filters):
        box = tk.Frame(parent, bg=WHITE, pady=10)
        box.pack(fill="x", pady=4)
        art = tk.Frame(box, bg=WHITE)
        art.pack()
        for name, h in (("snake_plant", 70), ("monstera_pot", 86), ("peace_lily", 78),
                        ("watering_can", 66)):
            theme.deco_label(art, name, 90, h, bg=WHITE).pack(side="left", padx=2,
                                                               anchor="s")
        tk.Label(box, text="No tasks match your filters." if has_tasks else "No tasks here yet.",
                 bg=WHITE, fg=TEXT, font=(theme.UI, 13, "bold")).pack(pady=(10, 2))
        tk.Label(box, text="Clear the search or pick different filters." if has_tasks
                 else "Use Add Task to schedule your first plant-care job.",
                 bg=WHITE, fg=TEXT, font=(theme.UI, 10)).pack()
        if has_tasks:
            ui.RoundButton(box, "Clear filters", clear_filters, kind="soft", icon="filter",
                           height=36, font=(theme.UI, 10, "bold"), icon_size=14
                           ).pack(pady=(10, 0))
        else:
            ui.RoundButton(box, "Add Task", lambda: self.nav_click("add_task"), icon="plus",
                           height=38, font=(theme.UI, 10, "bold"), icon_size=14
                           ).pack(pady=(10, 0))

    def task_thumbnail(self, parent, t, size=46, bg=WHITE):
        """The plant's uploaded picture, or the task-type icon if there is none."""
        path = self.plant_photo_path(t.get("photo"))
        img = None
        if path:
            try:
                mtime = os.path.getmtime(path)
            except OSError:
                mtime = None
            img = theme.round_photo(path, size, size, radius=12, mtime=mtime)
        if img is None:
            colour = theme.TASK_ICON_COLOURS.get(t["task_type"], SAGE)
            img = theme.badge(theme.TASK_ICON_NAMES.get(t["task_type"], "leaf"), size,
                              SAGE_LIGHT, colour, 0.5)
        lbl = tk.Label(parent, bg=bg, bd=0)
        if img is not None:
            lbl.config(image=img)
            lbl.image = img
        else:
            lbl.config(text="🌿", font=(theme.UI, 16))
        return lbl

    def _task_row(self, parent, t):
        """One task 'card' on the dashboard."""
        pending = t["status"] == "Pending"
        row = ui.RoundBox(parent, fill=WHITE, radius=14, border="#ece6d6", padx=12, pady=8)
        row.pack(fill="x", pady=3, padx=(0, 6))
        inner = row.inner
        inner.columnconfigure(1, weight=1)

        self.task_thumbnail(inner, t).grid(row=0, column=0, padx=(0, 12))

        info = tk.Frame(inner, bg=WHITE)
        info.grid(row=0, column=1, sticky="w")
        tk.Label(info, text=f"{t['task_type']}  ·  {t['plant_name']}", bg=WHITE, fg=TEXT,
                 font=(theme.UI, 11, "bold")).pack(anchor="w")
        if pending:
            due_text = describe_due(t["due"], date.today())
            due_fg = BAD if t["priority"] == "Overdue" else TEXT
        else:
            due_text, due_fg = f"Done {t['completed_on'] or ''}", MUTED
        line = tk.Frame(info, bg=WHITE)
        line.pack(anchor="w", pady=(2, 0))
        ui.icon_label(line, "calendar", 14, due_fg, bg=WHITE).pack(side="left", padx=(0, 5))
        extra = f"   ·   ID {t['plant_id']}"
        if t["repeat"] != "One-time":
            extra += f"   ·   ↻ {t['repeat']}"
        tk.Label(line, text=due_text, bg=WHITE, fg=due_fg,
                 font=(theme.UI, 10, "bold" if due_fg == BAD else "normal")).pack(side="left")
        tk.Label(line, text=extra, bg=WHITE, fg=MUTED, font=theme.F_SMALL).pack(side="left")

        pills = tk.Frame(inner, bg=WHITE)
        pills.grid(row=0, column=2, padx=8)
        fg, fill = PILL.get(t["priority"].lower(), PILL["completed"])
        ui.Pill(pills, t["priority"], fg, fill, bg=WHITE, min_width=88, height=22).pack(
            pady=(0, 3))
        fg, fill = PILL.get(t["status"].lower(), PILL["completed"])
        ui.Pill(pills, t["status"], fg, fill, bg=WHITE, min_width=88, height=22).pack()

        actions = tk.Frame(inner, bg=WHITE)
        actions.grid(row=0, column=5, padx=(8, 0))
        tid = t["id"]
        if pending:
            ui.RoundButton(actions, "Done", lambda: self.complete_task_by_id(tid),
                           kind="success", icon="check", height=32, padx=12, icon_size=14,
                           font=(theme.UI, 9, "bold")).pack(side="left", padx=2)
        ui.IconButton(actions, "edit", lambda: self.edit_task_by_id(tid), colour=DARK,
                      fill=SAGE_LIGHT, hover="#d4e7c8", size=32, icon_size=15
                      ).pack(side="left", padx=2)
        ui.IconButton(actions, "trash", lambda: self.delete_task_by_id(tid), colour=BAD,
                      fill="#fde6e3", hover="#f9d0cb", size=32, icon_size=15
                      ).pack(side="left", padx=2)

    def show_bell_summary(self, attention, overdue_n, upcoming_n):
        if attention:
            msg = (f"{attention} task{'s' if attention != 1 else ''} need attention "
                   f"({overdue_n} overdue).")
        elif upcoming_n:
            msg = f"Nothing urgent. {upcoming_n} upcoming task{'s' if upcoming_n != 1 else ''}."
        else:
            msg = "You are all caught up. 🌿"
        messagebox.showinfo("Reminders", msg)

    def complete_task_by_id(self, task_id):
        next_due = self.db.complete_task(task_id)
        self.refresh_passive_views()
        if next_due:
            messagebox.showinfo("Next task scheduled",
                                f"Task completed. The next one is scheduled for {next_due}.")

    def edit_task_by_id(self, task_id):
        self.editing_task_id = task_id
        self.switch_view("add_task")

    def delete_task_by_id(self, task_id):
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this task?"):
            self.db.delete_task(task_id)
            self.refresh_passive_views()
