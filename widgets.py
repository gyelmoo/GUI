"""Reusable GUI pieces: tables, pills, flowers, date picker, scrolling frame."""

import calendar
import math
import tkinter as tk
from datetime import date
from tkinter import ttk

from config import (BG, BORDER, COLUMNS, DARK, MID, MUTED, PILL, TAG_COLORS, TEXT, WHITE)

try:                                  # Pillow is only needed for profile pictures
    from PIL import Image, ImageDraw, ImageOps, ImageTk
    PIL_OK = True
except ImportError:
    PIL_OK = False


# ----------------------------------------------------------------------------
# Tables and pills
# ----------------------------------------------------------------------------
def make_tree(parent, keys, height, bg=BG):
    holder = tk.Frame(parent, bg=bg)
    holder.pack(fill="both", expand=True)
    tree = ttk.Treeview(holder, columns=keys, show="headings", height=height)
    scroll = ttk.Scrollbar(holder, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scroll.set)
    for key in keys:
        title, width, anchor = COLUMNS[key]
        tree.heading(key, text=title)
        tree.column(key, width=width, anchor=anchor, stretch=(key == "notes"))
    for tag, (fg, bg) in TAG_COLORS.items():
        tree.tag_configure(tag, foreground=fg, background=bg)
    tree.pack(side="left", fill="both", expand=True)
    scroll.pack(side="right", fill="y")
    return tree


def fill_tree(tree, tasks, keys):
    tree.delete(*tree.get_children())
    for t in tasks:
        tag = "done" if t["status"] == "Completed" else t["priority"].lower()
        tree.insert("", "end", iid=str(t["id"]),
                    values=[t.get(k) or "" for k in keys], tags=(tag,))


def pill(parent, text, key):
    fg, fill = PILL.get(key, PILL["completed"])
    return tk.Label(parent, text=text, fg=fg, bg=fill, padx=14, pady=3,
                    font=("Helvetica", 9, "bold"))


def limit_entry(entry, max_len):
    """Stop an Entry from accepting more than `max_len` characters."""
    entry.config(validate="key",
                 validatecommand=(entry.register(lambda proposed: len(proposed) <= max_len), "%P"))


def disc_mask(size):
    """Anti-aliased circular mask (drawn 4x larger, then shrunk)."""
    big = Image.new("L", (size * 4, size * 4), 0)
    ImageDraw.Draw(big).ellipse((0, 0, size * 4 - 1, size * 4 - 1), fill=255)
    return big.resize((size, size), Image.LANCZOS)


# ----------------------------------------------------------------------------
# Decorative flowers (drawn with Canvas shapes, no image files needed)
# ----------------------------------------------------------------------------
def _petal_points(cx, cy, length, width, angle):
    """Outline of a petal/leaf whose base is at (cx, cy), pointing along `angle` (radians)."""
    ca, sa = math.cos(angle), math.sin(angle)
    pts = []
    for i in range(16):
        t = 2 * math.pi * i / 16
        x = (math.cos(t) + 1) / 2 * length          # 0 (base) .. length (tip)
        y = math.sin(t) * width / 2
        pts += [cx + x * ca - y * sa, cy + x * sa + y * ca]
    return pts


def draw_leaf(canvas, x, y, length, angle_deg, colour):
    canvas.create_polygon(_petal_points(x, y, length, length * 0.42, math.radians(angle_deg)),
                          fill=colour, outline="", smooth=True)


def draw_flower(canvas, cx, cy, r, petals=6):
    for ring, size, colour in ((0.0, 1.0, "#f2a0b2"), (math.pi / petals, 0.7, "#f9c9d3")):
        for i in range(petals):
            a = 2 * math.pi * i / petals + ring
            canvas.create_polygon(_petal_points(cx, cy, r * size, r * size * 0.62, a),
                                  fill=colour, outline="", smooth=True)
    canvas.create_oval(cx - r * 0.2, cy - r * 0.2, cx + r * 0.2, cy + r * 0.2,
                       fill="#f3c64f", outline="")


def draw_cluster(canvas, ox, oy, sx, sy, scale=1.0):
    """A small bouquet growing out of the corner (ox, oy). sx / sy flip it (+1 or -1)."""
    def pos(x, y):
        return ox + sx * x * scale, oy + sy * y * scale

    def ang(a):
        r = math.radians(a)
        return math.degrees(math.atan2(sy * math.sin(r), sx * math.cos(r)))

    stems = [[(14, 0), (30, 55), (58, 105), (72, 150)],
             [(44, 0), (84, 38), (122, 66), (142, 92)],
             [(2, 30), (10, 70), (8, 100), (22, 128)]]
    for stem in stems:
        flat = [v for p in stem for v in pos(*p)]
        canvas.create_line(*flat, smooth=True, fill="#7aa874", width=max(1, round(2 * scale)))

    leaves = [(30, 55, 25, 60, "#8fbf8a"), (47, 92, 110, 52, "#a9d29c"),
              (84, 38, -15, 56, "#8fbf8a"), (112, 60, 70, 44, "#6fa874"),
              (14, 20, 80, 46, "#a9d29c"), (60, 8, 30, 50, "#6fa874"),
              (8, 70, 150, 38, "#8fbf8a")]
    for x, y, a, length, colour in leaves:
        px, py = pos(x, y)
        draw_leaf(canvas, px, py, length * scale, ang(a), colour)

    for x, y, r in ((72, 150, 28), (142, 92, 22), (22, 128, 15)):
        px, py = pos(x, y)
        draw_flower(canvas, px, py, r * scale)


def make_flower_canvas(parent, width, height, corners, bg, scale=1.0):
    """Canvas with flowers in the given corners, e.g. "bl", "tr" or "bl,br"."""
    canvas = tk.Canvas(parent, width=width, height=height, bg=bg, highlightthickness=0)
    anchors = {"tl": (0, 0, 1, 1), "tr": (width, 0, -1, 1),
               "bl": (0, height, 1, -1), "br": (width, height, -1, -1)}
    for corner in corners.split(","):
        ox, oy, sx, sy = anchors[corner.strip()]
        draw_cluster(canvas, ox, oy, sx, sy, scale)
    return canvas


# ----------------------------------------------------------------------------
# Date picker and scrolling container
# ----------------------------------------------------------------------------
class DatePicker(tk.Toplevel):
    """Pop-up month calendar. Calls on_pick(date) when the user presses OK."""

    def __init__(self, parent, initial, min_date, on_pick):
        super().__init__(parent)
        self.title("Select Due Date")
        self.configure(bg=WHITE)
        self.resizable(False, False)
        self.transient(parent.winfo_toplevel())
        self.selected = initial
        self.min_date = min_date
        self.on_pick = on_pick
        self.year, self.month = initial.year, initial.month

        top = tk.Frame(self, bg=WHITE, padx=18, pady=12)
        top.pack(fill="x")
        tk.Label(top, text="Select Due Date", bg=WHITE, fg=DARK,
                 font=("Helvetica", 13, "bold")).pack(side="left")
        tk.Button(top, text="✕", command=self.destroy, bg=WHITE, fg=MUTED, relief="flat",
                  activebackground="#eef2ef", cursor="hand2", bd=0).pack(side="right")

        box = tk.Frame(self, bg=WHITE, padx=18)
        box.pack()
        nav = tk.Frame(box, bg=WHITE)
        nav.pack(fill="x", pady=(0, 6))
        self.prev_btn = tk.Button(nav, text="‹", command=lambda: self.shift(-1), bg=WHITE,
                                  fg=TEXT, relief="flat", font=("Helvetica", 14, "bold"),
                                  cursor="hand2", activebackground="#eef2ef", width=3)
        self.prev_btn.pack(side="left")
        self.month_label = tk.Label(nav, bg=WHITE, fg=TEXT, font=("Helvetica", 11, "bold"))
        self.month_label.pack(side="left", expand=True)
        tk.Button(nav, text="›", command=lambda: self.shift(1), bg=WHITE, fg=TEXT,
                  relief="flat", font=("Helvetica", 14, "bold"), cursor="hand2",
                  activebackground="#eef2ef", width=3).pack(side="right")

        self.grid_frame = tk.Frame(box, bg=WHITE, highlightbackground=BORDER,
                                   highlightthickness=1, padx=6, pady=6)
        self.grid_frame.pack()

        buttons = tk.Frame(self, bg=WHITE, padx=18, pady=14)
        buttons.pack(fill="x")
        tk.Button(buttons, text="Cancel", command=self.destroy, bg="#e6f0e4", fg=TEXT,
                  relief="flat", font=("Helvetica", 10, "bold"), padx=26, pady=6,
                  cursor="hand2", activebackground="#d6e6d2").pack(side="left", expand=True,
                                                                  fill="x", padx=(0, 6))
        tk.Button(buttons, text="OK", command=self.confirm, bg=DARK, fg=WHITE, relief="flat",
                  font=("Helvetica", 10, "bold"), padx=26, pady=6, cursor="hand2",
                  activebackground=MID, activeforeground=WHITE).pack(side="left", expand=True,
                                                                    fill="x", padx=(6, 0))
        self.draw()

        # centre over the main window
        self.update_idletasks()
        root = parent.winfo_toplevel()
        x = root.winfo_rootx() + max(0, (root.winfo_width() - self.winfo_reqwidth()) // 2)
        y = root.winfo_rooty() + max(0, (root.winfo_height() - self.winfo_reqheight()) // 2)
        self.geometry(f"+{x}+{y}")
        self.after(50, self._grab)

    def _grab(self):
        try:
            self.grab_set()
            self.focus_set()
        except tk.TclError:
            pass

    def shift(self, months):
        index = self.year * 12 + (self.month - 1) + months
        self.year, self.month = index // 12, index % 12 + 1
        self.draw()

    def choose(self, day):
        self.selected = day
        self.draw()

    def confirm(self):
        self.on_pick(self.selected)
        self.destroy()

    def draw(self):
        self.month_label.config(text=f"{calendar.month_name[self.month]} {self.year}")
        # no going back to months that are entirely in the past
        self.prev_btn.config(state="disabled" if (self.year, self.month) <=
                             (self.min_date.year, self.min_date.month) else "normal")
        for child in self.grid_frame.winfo_children():
            child.destroy()
        for col, name in enumerate(("Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat")):
            tk.Label(self.grid_frame, text=name, bg=WHITE, fg=MUTED, width=4,
                     font=("Helvetica", 9)).grid(row=0, column=col, pady=(0, 4))
        weeks = calendar.Calendar(firstweekday=6).monthdayscalendar(self.year, self.month)
        today = date.today()
        for r, week in enumerate(weeks, start=1):
            for col, num in enumerate(week):
                if num == 0:
                    tk.Label(self.grid_frame, text="", bg=WHITE, width=4).grid(row=r, column=col)
                    continue
                day = date(self.year, self.month, num)
                is_sel = day == self.selected
                too_early = day < self.min_date
                if is_sel:
                    bg, fg = "#2f6f4a", WHITE
                elif day == today:
                    bg, fg = "#e6f0e4", DARK
                else:
                    bg, fg = WHITE, ("#b8c4bc" if too_early else TEXT)
                btn = tk.Button(self.grid_frame, text=str(num), width=3, relief="flat", bg=bg,
                                fg=fg, activebackground="#d6e6d2", font=("Helvetica", 10,
                                "bold" if is_sel else "normal"),
                                state="disabled" if too_early and not is_sel else "normal",
                                disabledforeground="#b8c4bc",
                                cursor="arrow" if too_early else "hand2",
                                command=lambda d=day: self.choose(d))
                btn.grid(row=r, column=col, padx=1, pady=1)


class ScrollFrame(tk.Frame):
    """A vertically scrolling container. Put widgets inside `.inner`."""

    def __init__(self, parent, bg=BG):
        super().__init__(parent, bg=bg)
        self.canvas = tk.Canvas(self, bg=bg, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.inner = tk.Frame(self.canvas, bg=bg)
        self._window = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        self.inner.bind("<Configure>", lambda e: self.canvas.configure(
            scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfigure(
            self._window, width=e.width))
        for seq in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            self.canvas.bind_all(seq, self._on_wheel, add="+")

    def _on_wheel(self, event):
        try:
            if not self.canvas.winfo_exists():
                return
            widget = self.winfo_containing(event.x_root, event.y_root)
            while widget is not None and widget is not self:
                widget = widget.master
            if widget is None:                      # pointer is not over this list
                return
            if isinstance(self.winfo_containing(event.x_root, event.y_root), ttk.Treeview):
                return                              # tables scroll by themselves
            if self.inner.winfo_reqheight() <= self.canvas.winfo_height():
                return
        except (tk.TclError, KeyError):
            return
        if event.num == 4:
            step = -1
        elif event.num == 5:
            step = 1
        else:
            step = -1 if event.delta > 0 else 1
        self.canvas.yview_scroll(step, "units")
