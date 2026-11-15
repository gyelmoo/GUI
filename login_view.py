"""Login / Create-account screen."""

import math
import tkinter as tk

import theme
import ui
from config import (BAD, CREAM, DARK, FIELD_BORDER, GOOD, MAX_PASSWORD, MAX_USERNAME,
                    MIN_USERNAME, MUTED, SAGE, TEXT, WARN, WHITE)
from helpers import password_checks, password_problem, username_problem
from widgets import limit_entry

if theme.PIL_OK:
    from PIL import Image, ImageDraw


def _login_background(w, h, panel_w):
    """Cream page with a deep-green welcome panel that has a soft curved edge."""
    k = 2
    img = Image.new("RGB", (w * k, h * k), CREAM)
    d = ImageDraw.Draw(img)
    # soft green hills along the bottom of the cream side
    d.ellipse((panel_w * k - 200 * k, h * k - 110 * k, w * k + 300 * k, h * k + 260 * k),
              fill="#eef3e0")
    d.ellipse((w * k - 520 * k, h * k - 150 * k, w * k + 400 * k, h * k + 300 * k),
              fill="#e5eed5")
    pts = [(0, 0)]
    steps = 60
    for i in range(steps + 1):
        y = h * i / steps
        x = panel_w - 36 + 48 * math.sin(math.pi * (i / steps) * 0.95)
        pts.append((x * k, y * k))
    pts.append((0, h * k))
    d.polygon(pts, fill=DARK)
    # a slightly lighter wave inside the panel
    d.ellipse((-260 * k, h * k * 0.62, panel_w * k * 0.9, h * k * 1.35), fill="#245a3f")
    return img.resize((w, h), Image.LANCZOS)


class LoginMixin:
    def show_login_screen(self):
        self.clear_root()
        self.stop_reminders()
        self.user = None
        self.current_view = None
        self.configure(bg=CREAM)

        page = tk.Canvas(self, bg=CREAM, highlightthickness=0, bd=0)
        page.pack(fill="both", expand=True)
        state = {"job": None, "bg": None, "size": None}

        # ----------------------------------------------------------- the card
        card = ui.RoundBox(page, fill=WHITE, radius=24, shadow=10, padx=44, pady=30,
                           width=500, bg=CREAM)
        body = card.inner

        title_row = tk.Frame(body, bg=WHITE)
        title_row.pack(pady=(0, 2))
        ui.icon_label(title_row, "sprout", 30, DARK, bg=WHITE).pack(side="left", padx=(0, 10))
        tk.Label(title_row, text="Plant Care Scheduler", bg=WHITE, fg=DARK,
                 font=(theme.UI, 20, "bold")).pack(side="left")
        tk.Label(body, text="Welcome back! Sign in to manage your plants.", bg=WHITE,
                 fg=TEXT, font=(theme.UI, 11)).pack(pady=(2, 18))

        # Username ---------------------------------------------------------
        tk.Label(body, text="Username", bg=WHITE, fg=TEXT,
                 font=theme.F_LABEL).pack(anchor="w")
        username_var = tk.StringVar()
        username_field, username_entry = ui.entry_field(
            body, icon="user", placeholder="Enter your username", textvariable=username_var,
            icon_colour=DARK)
        username_field.pack(fill="x", pady=(6, 2))
        limit_entry(username_entry, MAX_USERNAME)

        username_hint = tk.Label(body, text="", bg=WHITE, fg=MUTED,
                                 font=theme.F_SMALL, anchor="w")
        username_hint.pack(fill="x", pady=(0, 8))

        # Password ---------------------------------------------------------
        tk.Label(body, text="Password", bg=WHITE, fg=TEXT,
                 font=theme.F_LABEL).pack(anchor="w")
        password_row = tk.Frame(body, bg=WHITE)
        password_row.pack(fill="x", pady=(6, 4))
        password_var = tk.StringVar()
        password_field, password_entry = ui.entry_field(
            password_row, icon="lock", placeholder="Enter your password", show="•",
            textvariable=password_var, icon_colour=DARK)
        password_field.pack(side="left", fill="x", expand=True)
        limit_entry(password_entry, MAX_PASSWORD)

        show_password = tk.BooleanVar(value=False)

        def toggle_password():
            password_entry.config(show="" if show_password.get() else "•")

        tk.Checkbutton(password_row, text="Show", variable=show_password,
                       command=toggle_password, bg=WHITE, fg=TEXT, selectcolor=WHITE,
                       activebackground=WHITE, activeforeground=DARK,
                       font=(theme.UI, 10), cursor="hand2", bd=0, highlightthickness=0
                       ).pack(side="right", padx=(10, 0))

        password_hint = tk.Label(body, text="", bg=WHITE, fg=MUTED, font=theme.F_SMALL,
                                 anchor="w", justify="left", wraplength=400)
        password_hint.pack(fill="x")

        error_label = tk.Label(body, text="", bg=WHITE, fg=BAD, wraplength=400,
                               justify="left", font=(theme.UI, 9, "bold"), anchor="w")
        error_label.pack(fill="x", pady=(2, 8))

        fields = {username_entry: username_field, password_entry: password_field}

        def set_border(entry, colour):
            fields[entry].set_border(colour)

        def read_fields():
            # "  Tenzin   Lhaden " -> "Tenzin Lhaden"
            return " ".join(username_entry.get().split()), password_entry.get()

        def handle_login(event=None):
            username, password = read_fields()
            if not username or not password:
                error_label.config(text="Please enter your username and password.")
                return
            user = self.db.verify_user(username, password)
            if user is None:
                error_label.config(text="Incorrect username or password.")
                return
            self.start_session(user)

        def handle_register():
            username, password = read_fields()
            problem = username_problem(username)
            if problem:
                error_label.config(text="Username: " + problem)
                set_border(username_entry, BAD)
                username_entry.focus_set()
                return
            problem = password_problem(password)
            if problem:
                error_label.config(text=problem)
                set_border(password_entry, BAD)
                password_entry.focus_set()
                return
            if not self.db.create_user(username, password):
                error_label.config(text="That username is already registered.")
                return
            user = self.db.verify_user(username, password)
            self.start_session(user)

        login_btn = ui.RoundButton(body, "Login  →", handle_login, kind="primary", height=46,
                                   radius=12, font=(theme.UI, 12, "bold"))
        login_btn.pack(fill="x", pady=(2, 10))
        register_btn = ui.RoundButton(body, "Create a new account", handle_register,
                                      kind="outline", height=46, radius=12,
                                      font=(theme.UI, 11, "bold"))
        register_btn.pack(fill="x")

        tk.Label(body, text="New user? Pick a username (letters only) and a strong password.\n"
                            "The button turns green when everything is valid.",
                 bg=WHITE, fg=MUTED, font=theme.F_SMALL, justify="center").pack(pady=(14, 0))

        card_id = page.create_window(0, 0, window=card, anchor="center")

        # ------------------------------------------------- background drawing
        def draw(w, h):
            state["job"] = None
            if w < 50 or h < 50:
                return
            panel_w = max(430, int(w * 0.37))
            page.delete("deco")
            if theme.PIL_OK:
                bg = theme.photo(_login_background(w, h, panel_w))
                state["bg"] = bg
                page.create_image(0, 0, image=bg, anchor="nw", tags="deco")
            else:
                page.create_rectangle(0, 0, panel_w, h, fill=DARK, outline="", tags="deco")

            def img(name, x, y, width, height, anchor, fade=1.0, flip=False):
                pic = theme.asset(name, width, height, fade, flip)
                if pic is not None:
                    page.create_image(x, y, image=pic, anchor=anchor, tags="deco")

            cx = panel_w / 2 - 10
            # left panel decorations
            img("sidebar_monstera", -20, h + 10, 220, 220, "sw")
            img("sidebar_leaves", -10, h * 0.30, 140, 170, "nw", flip=True)
            img("shelf_pothos", panel_w - 30, h + 6, 250, 250, "s")
            img("heart_pot", panel_w - 210, h + 4, 150, 150, "s")
            # cream side: fill the strips beside the card with hanging plants
            card_w, card_h = 500, card.winfo_reqheight()
            right_cx = panel_w + (w - panel_w) / 2 + 10
            card_l, card_r = right_cx - card_w / 2, right_cx + card_w / 2
            room_top = h / 2 - card_h / 2 - 6
            room_bottom = h - (h / 2 + card_h / 2) - 4
            gap_l0 = panel_w + 18                 # just right of the green curve
            gap_l = card_l - 14 - gap_l0          # empty strip left of the card
            gap_r = w - card_r - 14               # empty strip right of the card

            def vine(x, height, segments, flip=False, max_w=None, anchor="nw", y=-10):
                """Hang a long vine from the top edge, never wider than max_w."""
                if not theme.PIL_OK:
                    return
                if max_w is not None:
                    if max_w < 30:
                        return
                    height = min(height, max_w / theme.long_vine_ratio(segments))
                pic = theme.long_vine(height, segments, flip)
                if pic is not None:
                    page.create_image(x, y, image=pic, anchor=anchor, tags="deco")

            if gap_l > 50:
                # a curtain of trailing vines between the green panel and the card
                limit = card_l - 10
                vine(gap_l0 - 6, h * 0.55, 3, max_w=limit - gap_l0 + 6)
                x2 = gap_l0 + gap_l * 0.40
                vine(x2, h * 0.36, 2, flip=True, max_w=limit - x2)
                if gap_l > 120:
                    img("flower_branch", gap_l0 + gap_l * 0.18, -10,
                        min(gap_l * 0.75, 200), h * 0.30, "nw")

            if gap_r > 50:
                # a bigger hanging pot, with a vine trailing down from it
                pot_x = card_r + 14 + gap_r / 2
                pot = theme.asset("hanging_basket", min(gap_r - 6, 250), h * 0.5)
                pot_h = pot.height() if pot is not None else 0
                vine(pot_x + 6, h * 0.58 - pot_h * 0.6, 2, flip=True, anchor="n",
                     y=pot_h * 0.6, max_w=gap_r - 4)
                if pot is not None:
                    page.create_image(pot_x, -6, image=pot, anchor="n", tags="deco")

            if room_top > 80:                     # a small pot above the card
                img("hanging_pearls", card_r - 70, -4, 120, min(200, room_top + 4), "n")
            if room_bottom > 50:
                img("shelf_trio", w - 10, h + 4, 330, min(200, room_bottom), "se")
            img("pink_flowers", panel_w + 60, h + 6, 120, 120, "s")

            # welcome text
            logo = theme.asset("logo_light", 96, 96)
            top = h * 0.10
            if logo is not None:
                page.create_image(cx, top, image=logo, anchor="n", tags="deco")
            page.create_text(cx, top + 132, text="Grow with care.", fill=WHITE,
                             font=(theme.UI, 30, "bold"), tags="deco")
            page.create_text(cx, top + 192, text="Plan your plant care.\n"
                             "Stay consistent. Keep every plant thriving.", fill="#e3efe2",
                             font=(theme.UI, 12), justify="center", tags="deco")
            for i, (icon, text) in enumerate((("bell", "Smart reminders"),
                                              ("calendar", "Daily & weekly routines"),
                                              ("chart", "Progress tracking"))):
                y = top + 262 + i * 56
                chip = theme.rounded_rect(250, 44, 22, "#2f6648")
                if chip is not None:
                    page.create_image(cx, y, image=chip, tags="deco")
                ic = theme.icon(icon, 20, "#e8f3e4")
                if ic is not None:
                    page.create_image(cx - 102, y, image=ic, anchor="w", tags="deco")
                page.create_text(cx - 70, y, text=text, fill=WHITE, anchor="w",
                                 font=(theme.UI, 11), tags="deco")

            page.tag_lower("deco")
            page.coords(card_id, right_cx, h / 2)

        def on_resize(event):
            if state["size"] == (event.width, event.height):
                return
            state["size"] = (event.width, event.height)
            if state["job"] is not None:
                page.after_cancel(state["job"])
            state["job"] = page.after(60, lambda: draw(event.width, event.height))

        page.bind("<Configure>", on_resize)

        # ---- live validation: runs on every keystroke -------------------------
        def update_register_button():
            # The button is always clickable (a click explains what is missing);
            # it turns solid green once everything is valid.
            ok = (username_problem(username_var.get()) is None
                  and password_problem(password_var.get()) is None)
            if ok:
                register_btn.set_colors(SAGE, WHITE, "#5c9548")
            else:
                register_btn.set_colors(WHITE, DARK, "#eef5ea", DARK)

        def on_username_change(*_):
            error_label.config(text="")
            text = username_var.get()
            if not text.strip():
                username_hint.config(text="", fg=MUTED)
                set_border(username_entry, FIELD_BORDER)
            elif any(not (c.isalpha() or c == " ") for c in text):
                username_hint.config(text="✗ " + username_problem(text), fg=BAD)
                set_border(username_entry, BAD)
            elif username_problem(text):
                username_hint.config(text=f"Keep going - at least {MIN_USERNAME} letters.",
                                     fg=WARN)
                set_border(username_entry, WARN)
            elif self.db.username_exists(" ".join(text.split())):
                username_hint.config(text="✓ Account found - enter your password and log in.",
                                     fg=GOOD)
                set_border(username_entry, SAGE)
            else:
                username_hint.config(text="✓ Username is free - you can create a new account.",
                                     fg=GOOD)
                set_border(username_entry, SAGE)
            update_register_button()

        def on_password_change(*_):
            error_label.config(text="")
            text = password_var.get()
            checks = password_checks(text)
            missing = [label for label, ok in checks if not ok]
            if not text:
                password_hint.config(text="")
                set_border(password_entry, FIELD_BORDER)
            elif not missing:
                password_hint.config(text="✓ Strong password", fg=GOOD)
                set_border(password_entry, SAGE)
            else:
                # only matters for new accounts, so it is a hint, not an error
                password_hint.config(text="New account needs: " + ", ".join(missing), fg=WARN)
                set_border(password_entry, WARN)
            update_register_button()

        username_var.trace_add("write", on_username_change)
        password_var.trace_add("write", on_password_change)
        on_username_change()
        on_password_change()

        username_entry.focus_set()
        username_entry.bind("<Return>", handle_login)
        password_entry.bind("<Return>", handle_login)