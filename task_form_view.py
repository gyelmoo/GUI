"""Add Task / Edit Task form (live validation, unique Plant ID check, plant picture)."""

import os
import tkinter as tk
from datetime import date, timedelta
from tkinter import filedialog, messagebox

import theme
import ui
from config import (BAD, BG, DARK, FIELD_BORDER, GOOD, MAX_NOTES, MAX_PLANT_ID, MAX_PLANT_NAME,
                    MIN_PLANT_NAME,
                    MINT_SOFT, MUTED, ONE_TASK_PER_PLANT_ID, PRIORITIES, REPEATS, SAGE,
                    SAGE_LIGHT, TASK_TYPES, TEXT, URGENT_WINDOW_DAYS, WARN, WHITE)
from helpers import (describe_due, due_date_problem, notes_problem, parse_date,
                     plant_id_problem, plant_name_problem)
from widgets import DatePicker, ScrollFrame, limit_entry

NEUTRAL_BORDER = FIELD_BORDER
PREVIEW_W, PREVIEW_H = 250, 150

TYPE_HINTS = {"Watering": "Watering - give the soil a good drink.",
              "Fertilizing": "Fertilizing - feed the plant.",
              "Pruning": "Pruning - trim dead or overgrown parts.",
              "Repotting": "Repotting - move it to a fresh pot.",
              "Other": "Other plant-care job."}
PRIORITY_HINTS = {"Urgent": "Urgent - shown first, reminded right away.",
                  "Routine": f"Routine - becomes Urgent {URGENT_WINDOW_DAYS} day before it is due.",
                  "Optional": "Optional - nice to do, no rush."}
REPEAT_HINTS = {"One-time": "One-time - happens once.",
                "Daily": "Daily - repeats every day when completed.",
                "Weekly": "Weekly - repeats every week when completed."}


class TaskFormMixin:
    def plant_id_conflict(self, plant_id, plant_name, editing_task_id):
        """Unique Plant ID rule. Returns an error message, or None if the ID can be used.

        * Two pending tasks can never share a Plant ID (when ONE_TASK_PER_PLANT_ID is True).
        * An ID that already belongs to a plant with a DIFFERENT name cannot be reused.
        IDs are compared without upper/lower case, so P1 and p1 are the same ID.
        """
        existing = self.db.find_plant(self.user["id"], plant_id)
        if existing is None:
            return None
        uid, pid = self.user["id"], existing["plant_id"]
        if ONE_TASK_PER_PLANT_ID:
            if self.db.count_plant_tasks(uid, pid, editing_task_id, pending_only=True):
                used_by = self.db.plant_task_label(uid, pid, editing_task_id)
                return (f"Plant ID '{pid}' is already used ({used_by}). "
                        "Each task needs a different Plant ID.")
        elif self.db.count_plant_tasks(uid, pid, editing_task_id) == 0:
            return None
        if plant_name and plant_name.lower() != existing["plant_name"].lower():
            return ("This Plant ID is already taken.")
        return None

    def render_add_task(self):
        editing = None
        if self.editing_task_id is not None:
            editing = next((t for t in self.load_tasks()
                            if t["id"] == self.editing_task_id), None)
            if editing is None:
                self.editing_task_id = None

        self.page_header("Edit Task" if editing else "Add Task",
                         "Keep every plant on schedule", icon="leaf")

        # The form scrolls if the window is short; the buttons stay fixed at the bottom.
        scroll = ScrollFrame(self.content_area, bg=BG)
        main = ui.card(scroll.inner, padx=24, pady=16)
        main.pack(fill="x", padx=(0, 8), pady=(0, 6))
        holder = main.inner
        holder.columnconfigure(0, weight=1)

        form = tk.Frame(holder, bg=WHITE)
        form.grid(row=0, column=0, sticky="nsew", padx=(0, 22))
        form.columnconfigure(0, weight=1, uniform="col")
        form.columnconfigure(1, weight=1, uniform="col")

        fields = {}                                   # entry/text widget -> its rounded box

        def label(text, icon, row, col, span=1, colour=SAGE):
            box = tk.Frame(form, bg=WHITE)
            box.grid(row=row, column=col, columnspan=span, sticky="w", pady=(0, 6),
                     padx=(0, 18) if col == 0 else 0)
            ui.icon_label(box, icon, 20, colour, bg=WHITE).pack(side="left", padx=(0, 8))
            tk.Label(box, text=text, bg=WHITE, fg=TEXT, font=(theme.UI, 12, "bold")
                     ).pack(side="left")

        def error_label(row, col, span=1):
            lbl = tk.Label(form, text="", bg=WHITE, fg=BAD, font=theme.F_SMALL,
                           anchor="w", justify="left", wraplength=380)
            lbl.grid(row=row, column=col, columnspan=span, sticky="w",
                     padx=(0, 18) if col == 0 else 0, pady=(2, 6))
            return lbl

        def place(widget, row, col, span=1):
            widget.grid(row=row, column=col, columnspan=span, sticky="ew",
                        padx=(0, 18) if (col == 0 and span == 1) else 0)

        def set_border(widget, colour):
            fields[widget].set_border(colour)

        # Plant ID / Plant Name ----------------------------------------------
        label("Plant ID *", "leaf", 0, 0)
        f, plant_id_entry = ui.entry_field(form, icon="leaf", placeholder="Enter plant ID (numbers only)",
                                           bg=WHITE)
        place(f, 1, 0)
        fields[plant_id_entry] = f
        limit_entry(plant_id_entry, MAX_PLANT_ID)
        plant_id_err = error_label(2, 0)

        label("Plant Name *", "leaf", 0, 1)
        f, plant_name_entry = ui.entry_field(form, icon="leaf",
                                             placeholder="Enter plant name", bg=WHITE)
        place(f, 1, 1)
        fields[plant_name_entry] = f
        limit_entry(plant_name_entry, MAX_PLANT_NAME)
        plant_name_err = error_label(2, 1)

        # Task Type / Due Date ------------------------------------------------
        label("Task Type *", "sprout", 3, 0)
        type_field, task_type_cb = ui.combo_field(form, TASK_TYPES, icon="drop", bg=WHITE, width=14)
        place(type_field, 4, 0)
        task_type_cb.set(TASK_TYPES[0])

        label("Due Date *", "calendar", 3, 1, colour=DARK)
        date_var = tk.StringVar(value=(date.today() + timedelta(days=1)).isoformat())
        date_field = ui.Field(form, bg=WHITE, padx=12, pady=4)
        place(date_field, 4, 1)
        date_entry = tk.Entry(date_field.inner, textvariable=date_var, state="readonly", width=12,
                              readonlybackground=WHITE, bd=0, relief="flat",
                              highlightthickness=0, fg=TEXT, font=(theme.UI, 11),
                              cursor="hand2")
        date_entry.pack(side="left", fill="x", expand=True, ipady=6)

        def open_calendar(event=None):
            try:
                current = parse_date(date_var.get())
            except ValueError:
                current = date.today()
            DatePicker(self, current, date.today(),
                       lambda picked: date_var.set(picked.isoformat()))

        ui.IconButton(date_field.inner, "calendar", open_calendar, colour=DARK,
                      fill=SAGE_LIGHT, hover="#d4e7c8", size=34, icon_size=18
                      ).pack(side="right")
        date_entry.bind("<Button-1>", open_calendar)
        type_msg = error_label(5, 0)
        date_err = error_label(5, 1)

        # Priority / Repeat ---------------------------------------------------
        label("Priority *", "star", 6, 0, colour="#e8b324")
        prio_field, priority_cb = ui.combo_field(form, PRIORITIES, icon="flag", bg=WHITE, width=14)
        place(prio_field, 7, 0)
        priority_cb.set("Routine")

        label("Repeat *", "repeat", 6, 1, colour=DARK)
        rep_field, repeat_cb = ui.combo_field(form, REPEATS, icon="repeat",
                                              icon_colour="#3b8fd6", bg=WHITE, width=14)
        place(rep_field, 7, 1)
        repeat_cb.set(REPEATS[0])

        def update_icons(*_):
            kind = task_type_cb.get()
            type_field.set_icon(theme.TASK_ICON_NAMES.get(kind, "leaf"),
                                theme.TASK_ICON_COLOURS.get(kind, SAGE))
            prio_field.set_icon("flag", theme.PRIORITY_FLAG.get(priority_cb.get(), SAGE))

        task_type_cb.bind("<<ComboboxSelected>>", update_icons, add="+")
        priority_cb.bind("<<ComboboxSelected>>", update_icons, add="+")

        prio_msg = error_label(8, 0)
        repeat_msg = error_label(8, 1)

        # Notes ---------------------------------------------------------------
        label("Notes", "notes", 9, 0, span=2, colour=DARK)
        notes_field = ui.Field(form, bg=WHITE, padx=12, pady=8)
        place(notes_field, 10, 0, span=2)
        notes_entry = tk.Text(notes_field.inner, height=2, width=30, font=(theme.UI, 11), bd=0,
                              relief="flat", highlightthickness=0, wrap="word", fg=TEXT,
                              bg=WHITE, insertbackground=DARK)
        notes_entry.pack(fill="both", expand=True)
        fields[notes_entry] = notes_field
        notes_err = tk.Label(form, text="", bg=WHITE, fg=MUTED, font=theme.F_SMALL, anchor="e")
        notes_err.grid(row=11, column=0, columnspan=2, sticky="e", pady=(4, 0))
        ready_label = tk.Label(form, text="", bg=WHITE, fg=MUTED, anchor="w",
                               font=(theme.UI, 10, "bold"), wraplength=620, justify="left")
        ready_label.grid(row=12, column=0, columnspan=2, sticky="w", pady=(6, 0))

        # Plant picture panel -------------------------------------------------
        photo_state = {"new": None, "remove": False}
        panel = ui.RoundBox(holder, fill=MINT_SOFT, radius=18, padx=16, pady=14, bg=WHITE,
                            width=300)
        panel.grid(row=0, column=1, sticky="ns")
        pbody = panel.inner
        top = tk.Frame(pbody, bg=MINT_SOFT)
        top.pack(fill="x")
        ui.icon_label(top, "camera", 30, DARK, bg=MINT_SOFT).pack(side="left", padx=(0, 10))
        title_box = tk.Frame(top, bg=MINT_SOFT)
        title_box.pack(side="left")
        tk.Label(title_box, text="Upload Plant Picture", bg=MINT_SOFT, fg=DARK,
                 font=(theme.UI, 12, "bold")).pack(anchor="w")
        tk.Label(title_box, text="Add a photo of your plant (optional)", bg=MINT_SOFT,
                 fg=TEXT, font=theme.F_SMALL).pack(anchor="w")

        drop = ui.RoundBox(pbody, fill="#f7fbf2", radius=14, border="#9cc28a", dash=True,
                           border_width=2, padx=10, pady=12, bg=MINT_SOFT, cursor="hand2")
        drop.pack(fill="x", pady=(12, 10))
        zone = drop.inner
        art = ui.badge_label(zone, "image", 54, "#dcebd1", DARK, bg="#f7fbf2", scale=0.6)
        art.pack()
        upload_title = tk.Label(zone, text="Click to upload", bg="#f7fbf2", fg=DARK,
                                font=(theme.UI, 12, "bold"))
        upload_title.pack(pady=(6, 0))
        tk.Label(zone, text="JPG or PNG, up to 8 MB", bg="#f7fbf2", fg=MUTED,
                 font=theme.F_SMALL).pack()

        prev_head = tk.Frame(pbody, bg=MINT_SOFT)
        prev_head.pack(fill="x")
        tk.Frame(prev_head, bg=SAGE, width=12, height=2).pack(side="left", padx=(0, 6))
        tk.Label(prev_head, text="Preview", bg=MINT_SOFT, fg=DARK,
                 font=(theme.UI, 10, "bold")).pack(side="left")

        preview_box = tk.Frame(pbody, bg=MINT_SOFT, width=PREVIEW_W, height=PREVIEW_H)
        preview_box.pack(pady=(6, 6))
        preview_box.pack_propagate(False)
        preview_img = tk.Label(preview_box, bg=MINT_SOFT, bd=0)
        preview_img.place(relx=0.5, rely=0.5, anchor="center")
        remove_btn = ui.IconButton(preview_box, "trash", lambda: remove_photo(),
                                   colour=BAD, fill=WHITE, hover="#fde6e3", size=32,
                                   icon_size=15, bg=MINT_SOFT)
        photo_note = tk.Label(pbody, text="", bg=MINT_SOFT, fg=MUTED, font=theme.F_SMALL,
                              wraplength=260, justify="center")
        photo_note.pack()

        def saved_photo_file():
            """The saved picture of the plant whose ID is typed (None if there is none)."""
            pid = plant_id_entry.get().strip()
            if not pid:
                return None
            plant = self.db.find_plant(self.user["id"], pid)
            if plant and self.plant_photo_path(plant.get("photo")):
                return plant["photo"]
            return None

        def refresh_photo(*_):
            img = None
            saved = None if photo_state["remove"] else saved_photo_file()
            if photo_state["new"] is not None and theme.PIL_OK:
                img = theme.pil_round_preview(photo_state["new"], PREVIEW_W, PREVIEW_H)
                photo_note.config(text="New picture - it is saved when you press Save Task.",
                                  fg=WARN)
            elif saved:
                path = self.plant_photo_path(saved)
                img = theme.round_photo(path, PREVIEW_W, PREVIEW_H, radius=14,
                                        mtime=os.path.getmtime(path))
                photo_note.config(text="Current picture of this plant.", fg=MUTED)
            elif photo_state["remove"]:
                photo_note.config(text="The picture will be removed when you save.", fg=WARN)
            else:
                photo_note.config(text="One picture per plant - it shows on every task "
                                       "for this plant.", fg=MUTED)
            if img is not None:
                preview_img.config(image=img, text="", width=PREVIEW_W, height=PREVIEW_H)
                preview_img.image = img
                remove_btn.place(relx=1.0, x=-8, y=8, anchor="ne")
                upload_title.config(text="Click to replace")
            else:
                empty = theme.rounded_rect(PREVIEW_W, PREVIEW_H, 14, "#f4f8ee", "#d6e4cb")
                preview_img.config(image=empty or "", text="No picture yet",
                                   compound="center", fg=MUTED, font=(theme.UI, 10),
                                   width=PREVIEW_W, height=PREVIEW_H)
                preview_img.image = empty
                remove_btn.place_forget()
                upload_title.config(text="Click to upload")

        def choose_photo(event=None):
            path = filedialog.askopenfilename(
                parent=self, title="Choose a plant picture",
                filetypes=[("Pictures", "*.png *.jpg *.jpeg"), ("All files", "*.*")])
            if not path:
                return
            try:
                photo_state["new"] = self.read_plant_photo(path)
            except ValueError as problem:
                messagebox.showerror("Could not use this picture", str(problem))
                return
            photo_state["remove"] = False
            refresh_photo()

        def remove_photo():
            photo_state["new"] = None
            photo_state["remove"] = True
            refresh_photo()

        drop.bind_all_children("<Button-1>", choose_photo)

        # Editing an existing task: fill in its values -------------------------
        if editing:
            plant_id_entry.insert(0, editing["plant_id"])
            plant_name_entry.insert(0, editing["plant_name"])
            task_type_cb.set(editing["task_type"])
            date_var.set(editing["due_date"])
            priority_cb.set(editing["base_priority"])      # the user's own choice, not the auto one
            repeat_cb.set(editing["repeat"])
            notes_entry.insert("1.0", editing["notes"])
            for e in (plant_id_entry, plant_name_entry):
                if hasattr(e, "refresh_hint"):
                    e.after_idle(e.refresh_hint)
        update_icons()

        # ---- validation -------------------------------------------------------
        def read_values():
            return dict(
                plant_id=plant_id_entry.get().strip(),
                plant_name=" ".join(plant_name_entry.get().split()),
                task_type=task_type_cb.get().strip(),
                due_date=date_var.get().strip(),
                base_priority=priority_cb.get().strip(),
                repeat=repeat_cb.get().strip(),
                notes=notes_entry.get("1.0", "end").strip(),
            )

        def show(lbl, kind, text):
            """kind: ok (green ✓), bad (red ✗), warn (orange), info (grey), or '' to clear."""
            colours = {"ok": GOOD, "bad": BAD, "warn": WARN, "info": MUTED}
            marks = {"ok": "✓ ", "bad": "✗ "}
            lbl.config(text=(marks.get(kind, "") + text) if kind else "",
                       fg=colours.get(kind, MUTED))

        def validate(strict=False):
            """Check every field, colour the boxes and show a message under each one.

            Live (strict=False): empty required boxes are not flagged red yet.
            On Save (strict=True): everything is checked. Returns a list of messages.
            """
            d = read_values()
            problems, missing = [], []

            # Plant ID - required, allowed characters, and unique
            msg = plant_id_problem(d["plant_id"]) if (d["plant_id"] or strict) else None
            if msg is None and d["plant_id"]:
                msg = self.plant_id_conflict(d["plant_id"], d["plant_name"],
                                             self.editing_task_id)
            if msg:
                show(plant_id_err, "bad", msg)
                problems.append(msg)
            elif d["plant_id"]:
                known = self.db.find_plant(self.user["id"], d["plant_id"])
                show(plant_id_err, "ok", "Plant ID is available." if known is None
                     else f"Plant ID is free to use for '{known['plant_name']}'.")
            else:
                show(plant_id_err, "info", "Numbers only, e.g. 1, 25 or 101.")
                missing.append("Plant ID")
            set_border(plant_id_entry, BAD if msg else
                       (GOOD if d["plant_id"] else NEUTRAL_BORDER))

            # Plant Name
            msg = plant_name_problem(d["plant_name"]) if (d["plant_name"] or strict) else None
            if msg:
                show(plant_name_err, "bad", msg)
                problems.append(msg)
            elif d["plant_name"]:
                show(plant_name_err, "ok", "Looks good.")
            else:
                show(plant_name_err, "info", f"At least {MIN_PLANT_NAME} characters.")
                missing.append("Plant Name")
            set_border(plant_name_entry, BAD if msg else
                       (GOOD if d["plant_name"] else NEUTRAL_BORDER))

            # Due date
            msg = due_date_problem(d["due_date"], date.today(),
                                   editing["due_date"] if editing else None)
            if msg:
                show(date_err, "bad", msg)
                problems.append(msg)
            else:
                due = parse_date(d["due_date"])
                show(date_err, "ok", f"{describe_due(due, date.today())} - "
                                     f"{due.strftime('%a, %d %b %Y')}")
            date_field.set_border(BAD if msg else GOOD)

            # Drop-downs: confirm the choice and explain what it means
            for value, allowed, name, lbl, box, hints in (
                    (d["task_type"], TASK_TYPES, "Task Type", type_msg, type_field, TYPE_HINTS),
                    (d["base_priority"], PRIORITIES, "Priority", prio_msg, prio_field,
                     PRIORITY_HINTS),
                    (d["repeat"], REPEATS, "Repeat", repeat_msg, rep_field, REPEAT_HINTS)):
                if value in allowed:
                    show(lbl, "ok", hints.get(value, f"{value} selected."))
                    box.set_border(GOOD)
                else:
                    show(lbl, "bad", f"Please choose a {name}.")
                    box.set_border(BAD)
                    problems.append(f"Please choose a {name}.")

            # Notes (optional)
            msg = notes_problem(d["notes"])
            left = MAX_NOTES - len(d["notes"])
            if msg:
                notes_err.config(text="✗ " + msg, fg=BAD)
                set_border(notes_entry, BAD)
                problems.append(msg)
            elif left <= 20:
                notes_err.config(text=f"{len(d['notes'])}/{MAX_NOTES} characters - "
                                      f"{left} left", fg=WARN)
                set_border(notes_entry, WARN)
            else:
                notes_err.config(text=f"{len(d['notes'])}/{MAX_NOTES} characters", fg=MUTED)
                set_border(notes_entry, GOOD if d["notes"] else NEUTRAL_BORDER)

            # Overall status + Save button colour
            if problems:
                n = len(problems)
                show(ready_label, "bad", f"{n} field{'s' if n != 1 else ''} need"
                                         f"{'' if n != 1 else 's'} attention before saving.")
                save_btn.set_colors("#7d9a86", WHITE, "#6c8a76")
            elif missing:
                show(ready_label, "info", "Still to fill in: " + ", ".join(missing) + ".")
                save_btn.set_colors("#7d9a86", WHITE, "#6c8a76")
            else:
                show(ready_label, "ok", "Everything looks good - ready to save.")
                save_btn.set_colors(DARK, WHITE, "#2b5d43")
            return problems

        def live(*_):
            validate(strict=False)

        last_pid = {"value": plant_id_entry.get().strip().lower()}

        def plant_id_typed(event=None):
            live()
            pid = plant_id_entry.get().strip().lower()
            if pid != last_pid["value"]:          # another plant: show its own picture
                last_pid["value"] = pid
                if photo_state["new"] is None:
                    photo_state["remove"] = False
                refresh_photo()

        plant_id_entry.bind("<KeyRelease>", plant_id_typed, add="+")
        plant_name_entry.bind("<KeyRelease>", live, add="+")
        notes_entry.bind("<KeyRelease>", live)
        date_var.trace_add("write", live)
        for cb in (task_type_cb, priority_cb, repeat_cb):
            cb.bind("<<ComboboxSelected>>", live, add="+")

        def cancel_action():
            self.editing_task_id = None
            self.switch_view("dashboard")

        def save_action():
            problems = validate(strict=True)
            if problems:
                messagebox.showerror("Validation Error", problems[0])
                return
            data = read_values()
            # Keep the spelling already stored for this plant (P1 and p1 are the same ID).
            existing = self.db.find_plant(self.user["id"], data["plant_id"])
            if existing:
                data["plant_id"] = existing["plant_id"]

            self.db.save_task(self.user["id"], data, task_id=self.editing_task_id)

            # Plant picture: save a new one, or remove the old one if asked
            photo_problem = None
            plant = self.db.find_plant(self.user["id"], data["plant_id"]) or {}
            try:
                if photo_state["new"] is not None:
                    self.store_plant_photo(data["plant_id"], photo_state["new"],
                                           plant.get("photo"))
                elif photo_state["remove"] and plant.get("photo"):
                    self.remove_plant_photo(data["plant_id"], plant.get("photo"))
            except Exception:
                photo_problem = "The task was saved, but the picture could not be saved."

            if photo_problem:
                messagebox.showwarning("Picture not saved", photo_problem)
            else:
                messagebox.showinfo("Success", "Task updated successfully!" if editing
                                    else "Task added successfully!")
            self.editing_task_id = None
            self.switch_view("dashboard")

        # ---- buttons + decorations under the card -----------------------------
        footer = tk.Canvas(self.content_area, bg=BG, highlightthickness=0, height=84)
        footer.pack(side="bottom", fill="x")
        scroll.pack(fill="both", expand=True)
        btns = tk.Frame(footer, bg=BG)
        ui.RoundButton(btns, "Cancel", cancel_action, kind="outline", icon="close",
                       height=50, width=170, radius=14, font=(theme.UI, 12, "bold")
                       ).pack(side="left", padx=(0, 16))
        save_btn = ui.RoundButton(btns, "Update Task" if editing else "Save Task",
                                  save_action, kind="primary", icon="check", height=50,
                                  width=220, radius=14, font=(theme.UI, 12, "bold"))
        save_btn.pack(side="left")
        validate(strict=False)
        refresh_photo()
        btn_id = footer.create_window(0, 14, window=btns, anchor="n")

        def layout_footer(event):
            w, h = event.width, event.height
            footer.delete("deco")
            footer.coords(btn_id, w / 2, 14)
            size = max(0, min(96, h - 2))
            if size > 40:
                for name, x, anchor, s in (("pink_flowers", 0, "sw", size),
                                           ("hibiscus", size * 0.85, "sw", size * 0.55),
                                           ("mascot_sign", w, "se", size)):
                    pic = theme.asset(name, int(s), int(s))
                    if pic is not None:
                        footer.create_image(x, h + 2, image=pic, anchor=anchor, tags="deco")

        footer.bind("<Configure>", layout_footer)