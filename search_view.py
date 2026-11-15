"""Search page: search box, filters, sorting and task cards with the plant's own photo."""

import os
import tkinter as tk
from tkinter import ttk

import theme
import ui
from config import (BAD, BG, DARK, IVORY, MAX_SEARCH, MUTED, PILL, SAGE_LIGHT, TEXT, WHITE)
from widgets import ScrollFrame, limit_entry

THUMB_W, THUMB_H = 112, 100
PRIORITY_ORDER = {"Overdue": 0, "Urgent": 1, "Routine": 2, "Optional": 3}
SORTS = ["Due Date", "Plant Name", "Priority", "Task Type"]


def photo_placeholder(w, h):
    """Neutral 'no photo' tile - shown only when the user has not uploaded a picture."""
    if not theme.PIL_OK:
        return None
    key = ("placeholder", w, h)
    if key not in theme._cache:
        base = theme.rounded_rect_pil(w, h, 14, "#f0f4ea", "#dbe5d2", 1)
        ic = theme.icon_pil("camera", 30, "#9db394", clear=theme.hex_rgb("#f0f4ea"))
        base.alpha_composite(ic, ((w - 30) // 2, (h - 30) // 2 - 9))
        from PIL import ImageDraw
        try:                                  # font_size needs Pillow 10.1 or newer
            ImageDraw.Draw(base).text((w / 2, h / 2 + 22), "No photo",
                                      fill=(120, 140, 115, 255), anchor="mm", font_size=12)
        except (TypeError, ValueError):
            pass
        theme._cache[key] = theme.photo(base)
    return theme._cache[key]


class SearchMixin:
    def render_search(self):
        self.page_header("Search Tasks", "Find any plant-care task in seconds", icon="search")

        # search row --------------------------------------------------------
        row1 = tk.Frame(self.content_area, bg=BG)
        row1.pack(fill="x", pady=(0, 10))
        search_field, search_entry = ui.entry_field(
            row1, icon="search", icon_colour=MUTED, placeholder="Search by plant name...")
        search_field.pack(side="left", fill="x", expand=True, padx=(0, 10))
        limit_entry(search_entry, MAX_SEARCH)

        # filter row --------------------------------------------------------
        row2 = tk.Frame(self.content_area, bg=BG)
        row2.pack(fill="x", pady=(0, 8))
        tasks_now = self.load_tasks()
        plant_names = sorted({t["plant_name"] for t in tasks_now})

        def chip(icon, caption, values, width):
            field = ui.Field(row2, icon=icon, padx=10, pady=3, radius=18)
            field.pack(side="left", padx=(0, 8))
            tk.Label(field.inner, text=caption, bg=WHITE, fg=TEXT,
                     font=(theme.UI, 10, "bold")).pack(side="left", padx=(0, 2))
            cb = ttk.Combobox(field.inner, values=values, state="readonly", width=width,
                                 style="Field.TCombobox", font=(theme.UI, 10))
            cb.pack(side="left", ipady=2)
            cb.set(values[0])
            return cb

        plant_cb = chip("leaf", "Plant Type:", ["All"] + plant_names, 10)
        status_cb = chip("calendar", "Status:", ["All", "Pending", "Completed"], 9)
        priority_cb = chip("flag", "Priority:", ["All", "Urgent", "Overdue", "Routine",
                                                 "Optional"], 8)
        sort_cb = chip("sort", "Sort by:", SORTS, 9)

        status_text = tk.Label(self.content_area, text="", bg=BG, fg=MUTED,
                               font=(theme.UI, 10))
        status_text.pack(anchor="w", pady=(0, 6))

        results = ScrollFrame(self.content_area, bg=BG)
        results.pack(fill="both", expand=True)
        grid = results.inner
        grid.columnconfigure(0, weight=1, uniform="card")
        grid.columnconfigure(1, weight=1, uniform="card")

        def run_search(event=None):
            q = search_entry.get().strip().lower()
            prio, stat, plant = priority_cb.get(), status_cb.get(), plant_cb.get()
            found = [
                t for t in self.load_tasks()
                if (not q or q in t["plant_id"].lower() or q in t["plant_name"].lower()
                    or q in t["task_type"].lower() or q in t["priority"].lower()
                    or q in t["notes"].lower())
                and (prio == "All" or t["priority"] == prio)
                and (stat == "All" or t["status"] == stat)
                and (plant == "All" or t["plant_name"] == plant)
            ]
            sort = sort_cb.get()
            if sort == "Plant Name":
                found.sort(key=lambda t: (t["plant_name"].lower(), t["due"]))
            elif sort == "Priority":
                found.sort(key=lambda t: (PRIORITY_ORDER.get(t["priority"], 9), t["due"]))
            elif sort == "Task Type":
                found.sort(key=lambda t: (t["task_type"], t["due"]))
            else:
                found.sort(key=lambda t: (t["due"], t["id"]))

            for child in grid.winfo_children():
                child.destroy()
            results.canvas.yview_moveto(0)
            status_text.config(text=f"Found {len(found)} matching task(s)."
                               if found else "No results found.")
            if not found:
                empty = tk.Frame(grid, bg=BG, pady=20)
                empty.grid(row=0, column=0, columnspan=2)
                theme.deco_label(empty, "watering_can_heart", 120, 100, bg=BG).pack()
                tk.Label(empty, text="No tasks match your search.", bg=BG, fg=TEXT,
                         font=(theme.UI, 12, "bold")).pack(pady=(8, 2))
                tk.Label(empty, text="Try another plant name or press Show All.", bg=BG,
                         fg=MUTED, font=(theme.UI, 10)).pack()
                return
            for i, t in enumerate(found):
                self._search_card(grid, t).grid(row=i // 2, column=i % 2, sticky="nsew",
                                                padx=(0 if i % 2 == 0 else 7,
                                                      7 if i % 2 == 0 else 6),
                                                pady=6)

        def show_all():
            search_entry.delete(0, "end")
            if hasattr(search_entry, "refresh_hint"):
                search_entry.refresh_hint()
            for cb in (plant_cb, status_cb, priority_cb):
                cb.set("All")
            sort_cb.set(SORTS[0])
            run_search()

        ui.RoundButton(row1, "Search", run_search, kind="primary", icon="search", height=46,
                       radius=14, width=140).pack(side="left", padx=(0, 8))
        ui.RoundButton(row1, "Show All", show_all, kind="outline", height=46, radius=14,
                       width=120).pack(side="left")
        search_entry.bind("<Return>", run_search)
        search_entry.bind("<KeyRelease>", lambda e: run_search(), add="+")
        for cb in (plant_cb, status_cb, priority_cb, sort_cb):
            cb.bind("<<ComboboxSelected>>", run_search, add="+")

        self.search_refresh = run_search
        run_search()

    def _search_card(self, parent, t):
        box = ui.RoundBox(parent, fill=IVORY, radius=18, shadow=5, padx=14, pady=12)
        inner = box.inner
        inner.columnconfigure(1, weight=1)

        # The plant's own uploaded picture (never a stock photo)
        img = None
        path = self.plant_photo_path(t.get("photo"))
        if path:
            try:
                img = theme.round_photo(path, THUMB_W, THUMB_H, radius=14,
                                        mtime=os.path.getmtime(path))
            except OSError:
                img = None
        if img is None:
            img = photo_placeholder(THUMB_W, THUMB_H)
        pic = tk.Label(inner, bg=IVORY, bd=0)
        if img is not None:
            pic.config(image=img)
            pic.image = img
        pic.grid(row=0, column=0, rowspan=4, sticky="nw", padx=(0, 14))

        tk.Label(inner, text=t["plant_name"], bg=IVORY, fg=TEXT, anchor="w",
                 font=(theme.UI, 14, "bold")).grid(row=0, column=1, sticky="w")
        sub = f"{t['task_type']}   ·   ID {t['plant_id']}"
        if t["repeat"] != "One-time":
            sub += f"   ·   ↻ {t['repeat']}"
        tk.Label(inner, text=sub, bg=IVORY, fg=MUTED, anchor="w",
                 font=(theme.UI, 10)).grid(row=1, column=1, sticky="w")

        pending = t["status"] == "Pending"
        due = tk.Frame(inner, bg=IVORY)
        due.grid(row=2, column=1, sticky="w", pady=(8, 0))
        overdue = t["priority"] == "Overdue"
        colour = BAD if overdue else TEXT
        ui.icon_label(due, "calendar", 15, colour if pending else MUTED, bg=IVORY
                      ).pack(side="left", padx=(0, 6))
        text = f"Due: {t['due'].strftime('%b %d, %Y')}"
        if pending and t.get("due_in"):
            text += f"  ({t['due_in']})"
        tk.Label(due, text=text, bg=IVORY, fg=colour if pending else MUTED,
                 font=(theme.UI, 10)).pack(side="left")

        bottom = tk.Frame(inner, bg=IVORY)
        bottom.grid(row=3, column=1, sticky="ew", pady=(8, 0))
        fg, fill = PILL.get(t["status"].lower(), PILL["completed"])
        status = "Pending" if pending else f"Completed {t['completed_on'] or ''}".strip()
        ui.Pill(bottom, status, fg, fill, bg=IVORY, height=24).pack(side="left")
        fg, fill = PILL.get(t["priority"].lower(), PILL["completed"])
        ui.Pill(bottom, t["priority"], fg, fill, bg=IVORY, height=28, min_width=78,
                font=(theme.UI, 10, "bold")).pack(side="right")

        menu_btn = ui.IconButton(inner, "dots", lambda: open_menu(), colour=DARK, fill=None,
                                 hover=SAGE_LIGHT, size=30, icon_size=16, bg=IVORY)
        menu_btn.grid(row=0, column=2, sticky="ne")

        def open_menu():
            menu = tk.Menu(self, tearoff=0, bg=WHITE, fg=TEXT, activebackground=SAGE_LIGHT,
                           activeforeground=DARK, font=(theme.UI, 10), bd=0)
            if pending:
                menu.add_command(label="✔  Mark as completed",
                                 command=lambda: self.complete_task_by_id(t["id"]))
            menu.add_command(label="✎  Edit task", command=lambda: self.edit_task_by_id(t["id"]))
            menu.add_separator()
            menu.add_command(label="🗑  Delete task",
                             command=lambda: self.delete_task_by_id(t["id"]))
            try:
                menu.tk_popup(menu_btn.winfo_rootx(), menu_btn.winfo_rooty() + 32)
            finally:
                menu.grab_release()

        # double-click a card to edit it
        box.bind_all_children("<Double-Button-1>", lambda e: self.edit_task_by_id(t["id"]))
        return box
