"""Summary / Report page."""

import calendar
import tkinter as tk
from datetime import date, timedelta

import theme
import ui
from config import (BG, DARK, MINT_SOFT, MUTED, PILL, PINK_SOFT, SAGE, TEXT, WHITE,
                    YELLOW_SOFT)
from dashboard_view import PLANT_TIPS
from helpers import parse_date
from widgets import ScrollFrame, fill_tree, make_tree

PERIODS = ["All Time", "This Month", "This Week"]
COMPLETED_COLOUR = "#6fa75a"
PENDING_COLOUR = "#f2aab4"
BAR_COLOURS = {"Urgent": "#e4645c", "Routine": "#e8b33a", "Optional": "#6fa75a"}


def period_range(period, today=None):
    today = today or date.today()
    if period == "This Month":
        last = calendar.monthrange(today.year, today.month)[1]
        return date(today.year, today.month, 1), date(today.year, today.month, last)
    if period == "This Week":
        start = today - timedelta(days=today.weekday())
        return start, start + timedelta(days=6)
    return None


def in_period(task, rng):
    """Pending tasks count by their due date, completed tasks by the day they were done."""
    if rng is None:
        return True
    day = task["due"]
    if task["status"] == "Completed" and task.get("completed_on"):
        try:
            day = parse_date(task["completed_on"])
        except ValueError:
            pass
    return rng[0] <= day <= rng[1]


def chart_bucket(task):
    """Priority group used by the bar chart.

    Overdue is a status, not a priority, so an overdue task is counted under the
    priority it was given. Everything else uses the priority shown in the app
    (a Routine task that is due very soon has been raised to Urgent).
    """
    return task["base_priority"] if task["priority"] == "Overdue" else task["priority"]


def nice_step(max_value):
    for step in (1, 2, 5, 10, 20, 25, 50, 100, 200, 500):
        if max_value / step <= 5:
            return step
    return max(1, max_value // 5)


class SummaryMixin:
    def render_summary(self):
        if self.summary_period not in PERIODS:
            self.summary_period = PERIODS[0]
        rng = period_range(self.summary_period)
        tasks = [t for t in self.load_tasks() if in_period(t, rng)]
        pending = [t for t in tasks if t["status"] == "Pending"]
        done = [t for t in tasks if t["status"] == "Completed"]
        total = len(tasks)
        pct = int(len(done) / total * 100) if total else 0
        rate = len(done) / total * 100 if total else 0.0
        rate_text = f"{rate:.1f}".rstrip("0").rstrip(".") + "%"

        header = self.page_header("Summary / Report", "Track your plant care progress",
                                  icon="chart", plant="hanging_pearls")
        period_field, period_cb = ui.combo_field(header.controls, PERIODS, icon="calendar",
                                                 icon_colour=DARK, width=11,
                                                 font=(theme.UI, 10, "bold"))
        period_field.pack(side="left")
        period_cb.set(self.summary_period)

        def change_period(event=None):
            self.summary_period = period_cb.get()
            self.switch_view("summary")

        period_cb.bind("<<ComboboxSelected>>", change_period)

        page = ScrollFrame(self.content_area, bg=BG)
        page.pack(fill="both", expand=True)
        body = page.inner
        body.config(padx=2)

        # ------------------------------------------------------- stat cards
        top = tk.Frame(body, bg=BG)
        top.pack(fill="x", pady=(2, 12), padx=(0, 8))
        metrics = [
            ("Total Tasks", str(total), MINT_SOFT, ("leaf", "#cfe4c4", DARK)),
            ("Pending Tasks", str(len(pending)), PINK_SOFT, ("clock", "#f8cdcd", "#c0392b")),
            ("Completed Tasks", str(len(done)), MINT_SOFT, ("check", DARK, WHITE)),
            ("Completion Rate", rate_text, YELLOW_SOFT, ("ring", None, None)),
        ]
        for i, (title, value, fill, art) in enumerate(metrics):
            box = ui.RoundBox(top, fill=fill, radius=18, shadow=5, padx=16, pady=12)
            box.grid(row=0, column=i, sticky="nsew", padx=(0 if i == 0 else 7, 0))
            top.columnconfigure(i, weight=1, uniform="metric")
            if art[0] == "ring":
                img = theme.ring(52, pct, "#e0a22e", "#f6e2b3")
                lbl = tk.Label(box.inner, bg=fill, bd=0)
                if img is not None:
                    lbl.config(image=img)
                    lbl.image = img
            else:
                lbl = ui.badge_label(box.inner, art[0], 52, art[1], art[2], bg=fill, scale=0.5)
            lbl.pack(side="left", padx=(0, 12))
            text_box = tk.Frame(box.inner, bg=fill)
            text_box.pack(side="left")
            tk.Label(text_box, text=title, bg=fill, fg=TEXT,
                     font=(theme.UI, 10)).pack(anchor="w")
            tk.Label(text_box, text=value, bg=fill, fg=TEXT,
                     font=theme.F_STAT).pack(anchor="w")

        # ------------------------------------------------- overall progress
        progress = ui.card(body, padx=20, pady=12, radius=16)
        progress.pack(fill="x", pady=(0, 12), padx=(0, 8))
        row = tk.Frame(progress.inner, bg=WHITE)
        row.pack(fill="x")
        ui.icon_label(row, "trophy", 24, "#e0a22e", bg=WHITE).pack(side="left", padx=(0, 10))
        tk.Label(row, text=f"Overall Completion Progress ({rate_text})", bg=WHITE, fg=TEXT,
                 font=(theme.UI, 11, "bold")).pack(side="left")
        tk.Label(row, text=f"{len(done)} / {total}", bg=WHITE, fg=TEXT,
                 font=(theme.UI, 11, "bold")).pack(side="right")
        ui.RoundProgress(progress.inner, value=pct, height=16, fill="#4f8a4f", track="#e6ecdf",
                         bg=WHITE).pack(fill="x", pady=(8, 2))

        # ----------------------------------------------------------- charts
        charts = tk.Frame(body, bg=BG)
        charts.pack(fill="x", pady=(0, 12), padx=(0, 8))
        charts.columnconfigure(0, weight=5, uniform="chart")
        charts.columnconfigure(1, weight=6, uniform="chart")

        # Donut: completed vs pending
        pie = ui.card(charts, padx=18, pady=14, radius=18)
        pie.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        ui.section_title(pie.inner, "Task Status Overview", "pending", bg=WHITE).pack(
            anchor="w")
        tk.Label(pie.inner, text="Completed and pending tasks", bg=WHITE, fg=MUTED,
                 font=theme.F_SMALL).pack(anchor="w", pady=(2, 6))
        size = 150
        donut = tk.Canvas(pie.inner, width=size, height=size, bg=WHITE, highlightthickness=0)
        donut.pack(pady=(2, 8))
        img = theme.donut(size, [(len(done), COMPLETED_COLOUR), (len(pending), PENDING_COLOUR)],
                          thickness=0.2)
        if img is not None:
            donut.image = img
            donut.create_image(size / 2, size / 2, image=img)
        elif total:                                    # no Pillow: plain canvas donut
            start = 90
            for value, colour in ((len(done), COMPLETED_COLOUR), (len(pending), PENDING_COLOUR)):
                extent = 360 * value / total
                donut.create_arc(4, 4, size - 4, size - 4, start=start, extent=-extent,
                                 fill=colour, outline=WHITE)
                start -= extent
            donut.create_oval(36, 36, size - 36, size - 36, fill=WHITE, outline=WHITE)
        donut.create_text(size / 2, size / 2 - 9, text=str(total), fill=DARK,
                          font=(theme.UI, 22, "bold"))
        donut.create_text(size / 2, size / 2 + 17, text="Total Tasks" if total else "No tasks",
                          fill=MUTED, font=(theme.UI, 9, "bold"))
        legend = tk.Frame(pie.inner, bg=WHITE)
        legend.pack()
        for label, value, colour in (("Completed", len(done), COMPLETED_COLOUR),
                                     ("Pending", len(pending), PENDING_COLOUR)):
            item = tk.Frame(legend, bg=WHITE)
            item.pack(side="left", padx=8)
            dot = tk.Canvas(item, width=14, height=14, bg=WHITE, highlightthickness=0)
            dot.create_oval(1, 1, 13, 13, fill=colour, outline=colour)
            dot.pack(side="left", padx=(0, 6))
            tk.Label(item, text=f"{label} ({value})", bg=WHITE, fg=TEXT,
                     font=(theme.UI, 10)).pack(side="left")

        # Bar chart: pending tasks by priority
        bars = ui.card(charts, padx=18, pady=14, radius=18)
        bars.grid(row=0, column=1, sticky="nsew")
        ui.section_title(bars.inner, "Pending Tasks by Priority", "chart", bg=WHITE
                         ).pack(anchor="w")
        overdue_n = sum(1 for t in pending if t["priority"] == "Overdue")
        recurring = sum(1 for t in pending if t["repeat"] != "One-time")
        chips = tk.Frame(bars.inner, bg=WHITE)
        chips.pack(anchor="w", pady=(6, 2))
        ui.Pill(chips, f"Overdue: {overdue_n}", *PILL["overdue"], bg=WHITE
                ).pack(side="left", padx=(0, 6))
        ui.Pill(chips, f"Repeating: {recurring}", *PILL["pending"], bg=WHITE).pack(side="left")
        tk.Label(bars.inner, text="Overdue tasks are counted under the priority they were "
                                  "given.", bg=WHITE, fg=MUTED, font=theme.F_SMALL,
                 wraplength=300, justify="left").pack(anchor="w", pady=(2, 0))
        counts = [(p, sum(1 for t in pending if chart_bucket(t) == p), BAR_COLOURS[p])
                  for p in ("Urgent", "Routine", "Optional")]
        bar_canvas = tk.Canvas(bars.inner, height=170, bg=WHITE, highlightthickness=0)
        bar_canvas.pack(fill="x", expand=True)
        bar_canvas.bind("<Configure>", lambda e: self._draw_bars(bar_canvas, e.width, counts))

        # Plant care tip
        charts.columnconfigure(2, weight=0)
        tip = ui.RoundBox(charts, fill=MINT_SOFT, radius=18, shadow=6, padx=14, pady=14,
                          width=200)
        tip.grid(row=0, column=2, sticky="nsew", padx=(10, 0))
        tip_head = tk.Frame(tip.inner, bg=MINT_SOFT)
        tip_head.pack(pady=(4, 0))
        ui.icon_label(tip_head, "bulb", 24, DARK, bg=MINT_SOFT).pack(side="left", padx=(0, 6))
        tk.Label(tip_head, text="Plant Care Tip", bg=MINT_SOFT, fg=DARK,
                 font=(theme.UI, 12, "bold")).pack(side="left")
        tip_text = PLANT_TIPS[(date.today().toordinal() + 1) % len(PLANT_TIPS)]
        tk.Label(tip.inner, text=tip_text, bg=MINT_SOFT, fg=TEXT, wraplength=165,
                 justify="center", font=(theme.UI, 10, "bold")).pack(pady=(10, 6))
        theme.deco_label(tip.inner, "cute_pot", 120, 110, bg=MINT_SOFT).pack(side="bottom")

        # ------------------------------------------------- completed history
        table = ui.card(body, padx=18, pady=14, radius=18)
        table.pack(fill="x", pady=(0, 8), padx=(0, 8))
        thead = tk.Frame(table.inner, bg=WHITE)
        thead.pack(fill="x", pady=(0, 8))
        ui.section_title(thead, "Completed Task History", "clipboard", bg=WHITE
                         ).pack(side="left")
        tk.Label(thead, text=f"{len(done)} completed", bg=WHITE, fg=MUTED,
                 font=(theme.UI, 10)).pack(side="right")
        keys = ["plant_id", "plant_name", "task_type", "due_date", "completed_on",
                "priority", "repeat", "notes"]
        holder = tk.Frame(table.inner, bg=WHITE)
        holder.pack(fill="both", expand=True)
        history = make_tree(holder, keys, height=6, bg=WHITE)
        fill_tree(history, sorted(done, key=lambda t: t["completed_on"] or "", reverse=True),
                  keys)
        if not done:
            tk.Label(table.inner, text="No completed tasks yet - mark a task as Done and it "
                                       "will appear here.", bg=WHITE, fg=MUTED,
                     font=theme.F_SMALL).pack(anchor="w", pady=(6, 0))

    def _draw_bars(self, canvas, width, counts):
        canvas.delete("all")
        height = int(canvas.cget("height"))
        left, right, top, bottom = 34, 10, 14, height - 30
        max_value = max([v for _, v, _ in counts] + [1])
        step = nice_step(max_value)
        top_value = max(step, ((max_value + step - 1) // step) * step)
        plot_h = bottom - top
        # grid lines + scale
        v = 0
        while v <= top_value:
            y = bottom - plot_h * v / top_value
            canvas.create_line(left, y, width - right, y, fill="#edf0e8")
            canvas.create_text(left - 10, y, text=str(v), fill=MUTED, anchor="e",
                               font=(theme.UI, 9))
            v += step
        slot = (width - left - right) / len(counts)
        bar_w = min(70, slot * 0.5)
        for i, (label, value, colour) in enumerate(counts):
            cx = left + slot * (i + 0.5)
            x1, x2 = cx - bar_w / 2, cx + bar_w / 2
            h = plot_h * value / top_value
            if value:
                img = theme.rounded_rect(int(bar_w), max(8, int(h)), 7, colour)
                if img is not None:
                    canvas.create_image(x1, bottom - max(8, int(h)), image=img, anchor="nw")
                    canvas.create_rectangle(x1, bottom - min(7, h), x1 + int(bar_w) - 1,
                                            bottom, fill=colour, outline="")
                    canvas._imgs = getattr(canvas, "_imgs", []) + [img]
                else:
                    canvas.create_rectangle(x1, bottom - h, x2, bottom, fill=colour, outline="")
            canvas.create_text(cx, bottom - h - 10, text=str(value),
                               fill=TEXT if value else MUTED, font=(theme.UI, 11, "bold"))
            canvas.create_text(cx, bottom + 16, text=label, fill=TEXT, font=(theme.UI, 10))
        canvas.create_line(left, bottom, width - right, bottom, fill="#cfd8c8")
