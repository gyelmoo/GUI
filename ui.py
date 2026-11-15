"""Rounded, themed widgets used by every screen.

Tkinter frames and buttons are always square, so the rounded look is made with
small Canvas widgets that draw a smooth rounded picture behind normal widgets.
"""

import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk

import theme
from config import (BORDER, CREAM, DARK, FIELD_BORDER, MID, MUTED, SAGE, SAGE_LIGHT, TEXT,
                    WHITE)


def _parent_bg(parent):
    try:
        return parent.cget("bg")
    except tk.TclError:
        return CREAM


# ----------------------------------------------------------------------------
# RoundBox - a rounded card. Put widgets inside `.inner`.
# ----------------------------------------------------------------------------
class RoundBox(tk.Canvas):
    def __init__(self, parent, fill=WHITE, radius=18, border=None, border_width=1, shadow=0,
                 padx=16, pady=14, fit=True, dash=False, bg=None, width=None, height=None,
                 cursor=""):
        # start tall enough that the inside is visible (Tk only lays out visible windows)
        super().__init__(parent, bg=bg or _parent_bg(parent), highlightthickness=0, bd=0,
                         width=width or 20, height=height or (2 * pady + shadow + 24),
                         cursor=cursor)
        self.fill, self.radius, self.border = fill, radius, border
        self.border_width, self.shadow, self.dash = border_width, shadow, dash
        self.padx, self.pady, self.fit = padx, pady, fit
        self.fixed_width = width is not None
        self._cw = self._ch = 0
        self._job = None
        self._img = None
        self._bg_item = self.create_image(0, 0, anchor="nw")
        self.inner = tk.Frame(self, bg=fill, cursor=cursor)
        self._win = self.create_window(padx, pady, window=self.inner, anchor="nw")
        self.bind("<Configure>", self._on_resize)
        self._checks = 0
        if fit:
            self.inner.bind("<Configure>", self._fit, add="+")
            self.after(20, self._fit_to_content)

    def _on_resize(self, event):
        self._cw, self._ch = event.width, event.height
        self.itemconfigure(self._win, width=max(1, event.width - 2 * self.padx))
        if not self.fit:
            self.itemconfigure(self._win,
                               height=max(1, event.height - 2 * self.pady - self.shadow))
        self._schedule()

    def _fit(self, event):
        want_h = event.height + 2 * self.pady + self.shadow
        if int(self.cget("height")) != want_h:
            self.config(height=want_h)
        if not self.fixed_width:
            want_w = self.inner.winfo_reqwidth() + 2 * self.padx
            if int(self.cget("width")) != want_w:
                self.config(width=want_w)

    def _fit_to_content(self):
        """Size the card from what its contents ask for (works even before it is shown)."""
        try:
            if not self.winfo_exists():
                return
            req_h = self.inner.winfo_reqheight()
            req_w = self.inner.winfo_reqwidth()
        except tk.TclError:
            return
        changed = False
        want_h = req_h + 2 * self.pady + self.shadow
        if req_h > 1 and int(self.cget("height")) != want_h:
            self.config(height=want_h)
            changed = True
        if not self.fixed_width and req_w > 1:
            want_w = req_w + 2 * self.padx
            if int(self.cget("width")) != want_w:
                self.config(width=want_w)
                changed = True
        self._checks = 0 if changed else self._checks + 1
        if self._checks < 4:                      # re-check while the contents settle
            self.after(60, self._fit_to_content)

    def _schedule(self):
        if self._job is None:
            self._job = self.after(10, self.redraw)

    def redraw(self):
        self._job = None
        w, h = self._cw or self.winfo_width(), self._ch or self.winfo_height()
        if w < 4 or h < 4:
            return
        img = theme.rounded_rect(w, h, self.radius, self.fill, self.border,
                                 self.border_width, self.shadow, self.dash)
        if img is not None:
            self._img = img
            self.itemconfigure(self._bg_item, image=img)
        else:                                       # no Pillow: plain rectangle
            self.delete("plain")
            self.create_rectangle(0, 0, w - 1, h - 1 - self.shadow, fill=self.fill,
                                  outline=self.border or self.fill, tags="plain")
            self.tag_lower("plain")

    def set_border(self, colour):
        if colour != self.border:
            self.border = colour
            self._schedule()

    def bind_all_children(self, sequence, func):
        """Bind an event on the card and everything inside it (e.g. a click)."""
        def walk(widget):
            widget.bind(sequence, func, add="+")
            for child in widget.winfo_children():
                walk(child)
        self.bind(sequence, func, add="+")
        walk(self.inner)


def card(parent, fill=WHITE, **kw):
    """Standard content card: white, rounded, soft shadow."""
    kw.setdefault("radius", 20)
    kw.setdefault("shadow", 6)
    kw.setdefault("padx", 20)
    kw.setdefault("pady", 16)
    return RoundBox(parent, fill=fill, **kw)


# ----------------------------------------------------------------------------
# RoundButton
# ----------------------------------------------------------------------------
BUTTON_KINDS = {
    #            fill        text      hover       border
    "primary": (DARK, WHITE, MID, None),
    "success": (SAGE, WHITE, "#5c9548", None),
    "danger": ("#e27667", WHITE, "#cc6153", None),
    "outline": (WHITE, DARK, "#eef5ea", DARK),
    "plain": (WHITE, TEXT, "#f1f5ee", FIELD_BORDER),
    "soft": (SAGE_LIGHT, DARK, "#d4e7c8", None),
    "nav": (DARK, "#e3efe5", "#2b5d43", None),
    "nav_active": (SAGE, WHITE, SAGE, None),
}


class RoundButton(tk.Canvas):
    def __init__(self, parent, text, command=None, kind="primary", icon=None, width=None,
                 height=40, font=theme.F_BUTTON, radius=None, padx=20, bg=None, align="center",
                 icon_size=18):
        super().__init__(parent, bg=bg or _parent_bg(parent), highlightthickness=0, bd=0,
                         cursor="hand2")
        self.command = command
        self.text, self.icon_name, self.font = text, icon, font
        self.align, self.icon_size, self.padx = align, icon_size, padx
        self.radius = height // 2 if radius is None else radius
        self._btn_state = "normal"
        self.hover = False
        self.fill, self.fg, self.hover_fill, self.border = BUTTON_KINDS[kind]
        f = tkfont.Font(font=font)
        natural = f.measure(text) + 2 * padx + ((icon_size + 10) if icon else 0)
        self.config(width=width or natural, height=height)
        self._cw, self._ch = width or natural, height
        self.bind("<Configure>", self._on_resize)
        self.bind("<Enter>", lambda e: self._set_hover(True))
        self.bind("<Leave>", lambda e: self._set_hover(False))
        self.bind("<ButtonRelease-1>", self._release)
        self.draw()

    def _on_resize(self, event):
        self._cw, self._ch = event.width, event.height
        self.draw()

    def _set_hover(self, value):
        self.hover = value
        self.draw()

    def _release(self, event):
        if self._btn_state != "normal":
            return
        if 0 <= event.x <= self._cw and 0 <= event.y <= self._ch:
            self.invoke()

    def invoke(self):
        if self._btn_state == "normal" and self.command:
            self.command()

    def draw(self):
        self.delete("all")
        w, h = self._cw, self._ch
        if self._btn_state == "disabled":
            fill, fg, border = "#dfe6dc", "#9aa89e", None
        else:
            fill = self.hover_fill if self.hover else self.fill
            fg, border = self.fg, self.border
        img = theme.rounded_rect(w, h, min(self.radius, h // 2), fill, border, 2 if border else 1)
        if img is not None:
            self._img = img
            self.create_image(0, 0, image=img, anchor="nw")
        else:
            self.create_rectangle(0, 0, w - 1, h - 1, fill=fill, outline=border or fill)
        f = tkfont.Font(font=self.font)
        tw = f.measure(self.text)
        ic = theme.icon(self.icon_name, self.icon_size, fg) if self.icon_name else None
        gap = 10 if self.text else 0
        content = tw + ((self.icon_size + gap) if ic else 0)
        x = self.padx if self.align == "w" else (w - content) / 2
        if ic is not None:
            self._icon = ic
            self.create_image(x, h / 2, image=ic, anchor="w")
            x += self.icon_size + gap
        self.create_text(x, h / 2, text=self.text, fill=fg, font=self.font, anchor="w")

    # -- helpers used by the screens ----------------------------------------
    def set_colors(self, fill, fg, hover=None, border=None):
        self.fill, self.fg = fill, fg
        self.hover_fill = hover or fill
        self.border = border
        self.draw()

    def set_kind(self, kind):
        self.set_colors(*BUTTON_KINDS[kind])

    def set_text(self, text):
        self.text = text
        self.draw()

    def set_state(self, state):
        self._btn_state = state
        self.config(cursor="hand2" if state == "normal" else "arrow")
        self.draw()


class IconButton(tk.Canvas):
    """Small round icon-only button (edit, delete, menu ...)."""

    def __init__(self, parent, icon, command, colour=DARK, fill=None, hover="#eef4ea",
                 size=32, icon_size=16, bg=None):
        super().__init__(parent, width=size, height=size, bg=bg or _parent_bg(parent),
                         highlightthickness=0, bd=0, cursor="hand2")
        self.command, self._btn_size = command, size
        self.icon_name, self.colour, self.icon_size = icon, colour, icon_size
        self.fill, self.hover_fill = fill, hover
        self.bind("<Enter>", lambda e: self.draw(True))
        self.bind("<Leave>", lambda e: self.draw(False))
        self.bind("<ButtonRelease-1>", lambda e: self.command())
        self.draw(False)

    def draw(self, hover):
        self.delete("all")
        fill = self.hover_fill if hover else self.fill
        if fill:
            img = theme.rounded_rect(self._btn_size, self._btn_size, self._btn_size // 2, fill)
            if img is not None:
                self._bg = img
                self.create_image(0, 0, image=img, anchor="nw")
        ic = theme.icon(self.icon_name, self.icon_size, self.colour)
        if ic is not None:
            self._ic = ic
            self.create_image(self._btn_size / 2, self._btn_size / 2, image=ic)
        else:
            self.create_text(self._btn_size / 2, self._btn_size / 2, text="•", fill=self.colour)


# ----------------------------------------------------------------------------
# Pills (priority / status labels)
# ----------------------------------------------------------------------------
class Pill(tk.Canvas):
    def __init__(self, parent, text, fg, fill, font=(theme.UI, 9, "bold"), padx=14, height=24,
                 bg=None, min_width=0):
        f = tkfont.Font(font=font)
        w = max(min_width, f.measure(text) + 2 * padx)
        super().__init__(parent, width=w, height=height, bg=bg or _parent_bg(parent),
                         highlightthickness=0, bd=0)
        img = theme.rounded_rect(w, height, height // 2, fill)
        if img is not None:
            self._img = img
            self.create_image(0, 0, image=img, anchor="nw")
        else:
            self.create_rectangle(0, 0, w, height, fill=fill, outline=fill)
        self.create_text(w / 2, height / 2, text=text, fill=fg, font=font)


# ----------------------------------------------------------------------------
# Input fields: a rounded white box holding an Entry / Combobox / Text
# ----------------------------------------------------------------------------
class Field(RoundBox):
    def __init__(self, parent, icon=None, icon_colour=SAGE, height=None, bg=None, padx=12,
                 pady=5, radius=12, fit=True):
        super().__init__(parent, fill=WHITE, radius=radius, border=FIELD_BORDER,
                         border_width=1, padx=padx, pady=pady, bg=bg, fit=fit, height=height)
        self.icon_label = None
        if icon:
            self.icon_label = tk.Label(self.inner, bg=WHITE, bd=0)
            self.icon_label.pack(side="left", padx=(0, 8))
            self.set_icon(icon, icon_colour)

    def set_icon(self, name, colour=SAGE):
        if self.icon_label is None:
            return
        img = theme.icon(name, 18, colour)
        if img is not None:
            self.icon_label.config(image=img)
            self.icon_label.image = img


def entry_field(parent, icon=None, placeholder="", show=None, textvariable=None,
                font=(theme.UI, 11), icon_colour=SAGE, bg=None):
    """Returns (field, entry). The placeholder is a separate grey label, so
    entry.get() never returns placeholder text."""
    field = Field(parent, icon=icon, icon_colour=icon_colour, bg=bg)
    holder = tk.Frame(field.inner, bg=WHITE)
    holder.pack(side="left", fill="x", expand=True)
    entry = tk.Entry(holder, bd=0, relief="flat", highlightthickness=0, bg=WHITE, fg=TEXT,
                     insertbackground=DARK, font=font, textvariable=textvariable, width=10)
    if show:
        entry.config(show=show)
    entry.pack(fill="x", ipady=6)
    if placeholder:
        hint = tk.Label(holder, text=placeholder, bg=WHITE, fg="#9aa89e", font=font,
                        anchor="w", cursor="xterm")

        def refresh(*_):
            if entry.get():
                hint.place_forget()
            else:
                hint.place(x=1, rely=0.5, anchor="w")
        hint.bind("<Button-1>", lambda e: entry.focus_set())
        for seq in ("<KeyRelease>", "<FocusIn>", "<FocusOut>"):
            entry.bind(seq, refresh, add="+")
        if textvariable is not None:
            textvariable.trace_add("write", refresh)
        entry.refresh_hint = refresh
        entry.after_idle(refresh)
    field.bind("<Button-1>", lambda e: entry.focus_set())
    field.inner.bind("<Button-1>", lambda e: entry.focus_set())
    return field, entry


def combo_field(parent, values, icon=None, width=18, textvariable=None, icon_colour=SAGE,
                bg=None, font=(theme.UI, 11)):
    """Returns (field, combobox). Read-only drop-down inside a rounded box."""
    field = Field(parent, icon=icon, icon_colour=icon_colour, bg=bg, pady=4)
    cb = ttk.Combobox(field.inner, values=values, state="readonly", width=width,
                      style="Field.TCombobox", font=font, textvariable=textvariable)
    cb.pack(side="left", fill="x", expand=True, ipady=3)
    return field, cb


def configure_combobox_style(root):
    style = ttk.Style(root)
    style.configure("Field.TCombobox", fieldbackground=WHITE, background=WHITE,
                    foreground=TEXT, bordercolor=WHITE, lightcolor=WHITE, darkcolor=WHITE,
                    arrowcolor=DARK, arrowsize=15, padding=(2, 2, 2, 2), relief="flat",
                    borderwidth=0)
    style.map("Field.TCombobox",
              fieldbackground=[("readonly", WHITE), ("disabled", "#f2f2ee")],
              background=[("readonly", WHITE), ("active", WHITE), ("pressed", WHITE)],
              foreground=[("readonly", TEXT)],
              selectbackground=[("readonly", WHITE), ("!focus", WHITE), ("focus", WHITE)],
              selectforeground=[("readonly", TEXT), ("!focus", TEXT), ("focus", TEXT)],
              bordercolor=[("focus", WHITE), ("active", WHITE)],
              lightcolor=[("focus", WHITE), ("active", WHITE)],
              darkcolor=[("focus", WHITE), ("active", WHITE)],
              arrowcolor=[("disabled", MUTED), ("active", MID)])
    root.option_add("*TCombobox*Listbox.font", (theme.UI, 10))
    root.option_add("*TCombobox*Listbox.selectBackground", SAGE)
    root.option_add("*TCombobox*Listbox.selectForeground", WHITE)
    root.option_add("*TCombobox*Listbox.background", WHITE)
    root.option_add("*TCombobox*Listbox.foreground", TEXT)


# ----------------------------------------------------------------------------
# Progress bar
# ----------------------------------------------------------------------------
class RoundProgress(tk.Canvas):
    def __init__(self, parent, value=0, height=14, fill=SAGE, track="#e3ecdb", width=200,
                 bg=None):
        super().__init__(parent, height=height, width=width, bg=bg or _parent_bg(parent),
                         highlightthickness=0, bd=0)
        self.value, self.fill, self.track, self.h = value, fill, track, height
        self.bind("<Configure>", lambda e: self.draw(e.width))

    def draw(self, w):
        self.delete("all")
        h = self.h
        track = theme.rounded_rect(w, h, h // 2, self.track)
        if track is None:
            self.create_rectangle(0, 0, w, h, fill=self.track, outline="")
            if self.value > 0:
                self.create_rectangle(0, 0, w * self.value / 100, h, fill=self.fill,
                                      outline="")
            return
        self._t = track
        self.create_image(0, 0, image=track, anchor="nw")
        fw = int(w * max(0, min(100, self.value)) / 100)
        if fw >= h:
            bar = theme.rounded_rect(fw, h, h // 2, self.fill)
            self._b = bar
            self.create_image(0, 0, image=bar, anchor="nw")
        elif fw > 0:
            self.create_oval(0, 0, h, h, fill=self.fill, outline="")


# ----------------------------------------------------------------------------
# Page header: icon + title + subtitle on the left, a hanging plant on the
# right, faded leaves behind. Extra controls go in `.controls`.
# ----------------------------------------------------------------------------
class PageHeader(tk.Canvas):
    def __init__(self, parent, title, subtitle, icon="leaf", height=104, plant="hanging_pothos",
                 title_font=theme.F_TITLE, subtitle_font=theme.F_PAGE_SUB, show_badge=True,
                 subtitle_colour=None):
        bg = _parent_bg(parent)
        super().__init__(parent, height=height, bg=bg, highlightthickness=0, bd=0)
        self.h = height
        self.plant_w = 0
        leaves = theme.asset("branch_leaves", 110, 110, fade=0.28, flip=True)
        if leaves is not None:
            self.create_image(-18, -22, image=leaves, anchor="nw")
        x = 0
        if show_badge:
            b = theme.badge(icon, 60, SAGE_LIGHT, DARK, 0.5)
            if b is not None:
                self.create_image(0, height / 2 - 6, image=b, anchor="w")
                x = 76
        self.title_id = self.create_text(x, height / 2 - 20, text=title, fill=DARK,
                                         font=title_font, anchor="w")
        self.sub_id = self.create_text(x + 2, height / 2 + 18, text=subtitle,
                                       fill=subtitle_colour or TEXT, font=subtitle_font,
                                       anchor="w")
        sprig = theme.asset("sprig_small", 26, 26)
        if sprig is not None:
            self._sprig = sprig
            self.after_idle(self._place_sprig)
        self.plant_img = theme.asset(plant, 112, height + 8) if plant else None
        if self.plant_img is not None:
            self.plant_w = self.plant_img.width()
            self.plant_id = self.create_image(0, -8, image=self.plant_img, anchor="ne")
        self.title_text, self.title_font, self.title_x = title, title_font, x
        self.controls = tk.Frame(self, bg=bg)
        self.controls_id = self.create_window(0, height / 2 - 6, window=self.controls,
                                              anchor="e")
        self.bind("<Configure>", self._layout)

    def _place_sprig(self):
        try:
            bbox = self.bbox(self.sub_id)
        except tk.TclError:
            return
        if bbox:
            self.create_image(bbox[2] + 8, (bbox[1] + bbox[3]) / 2, image=self._sprig,
                              anchor="w")

    def _layout(self, event):
        w = event.width
        if self.plant_img is not None:
            self.coords(self.plant_id, w + 4, -8)
        right = w - self.plant_w - 8
        self.coords(self.controls_id, right, self.h / 2 - 6)
        # shrink a long title (e.g. a long user name) so it never runs under the buttons
        room = right - self.controls.winfo_reqwidth() - 16 - self.title_x
        family, size = self.title_font[0], self.title_font[1]
        styles = self.title_font[2:]
        while size > 14 and tkfont.Font(font=(family, size) + styles).measure(
                self.title_text) > room:
            size -= 1
        self.itemconfigure(self.title_id, font=(family, size) + styles)

    def set_subtitle(self, text, colour=None):
        self.itemconfigure(self.sub_id, text=text)
        if colour:
            self.itemconfigure(self.sub_id, fill=colour)


def section_title(parent, text, icon="leaf", bg=None, font=theme.F_H2, colour=DARK):
    """Small heading with a coloured icon in front."""
    bg = bg or _parent_bg(parent)
    row = tk.Frame(parent, bg=bg)
    img = theme.icon(icon, 18, SAGE)
    if img is not None:
        lbl = tk.Label(row, image=img, bg=bg)
        lbl.image = img
        lbl.pack(side="left", padx=(0, 8))
    tk.Label(row, text=text, bg=bg, fg=colour, font=font).pack(side="left")
    return row


def icon_label(parent, name, size=18, colour=SAGE, bg=None):
    bg = bg or _parent_bg(parent)
    img = theme.icon(name, size, colour)
    lbl = tk.Label(parent, bg=bg, bd=0)
    if img is not None:
        lbl.config(image=img)
        lbl.image = img
    return lbl


def badge_label(parent, name, size, circle, colour, bg=None, scale=0.52):
    bg = bg or _parent_bg(parent)
    img = theme.badge(name, size, circle, colour, scale)
    lbl = tk.Label(parent, bg=bg, bd=0)
    if img is not None:
        lbl.config(image=img)
        lbl.image = img
    return lbl


BORDER_LIGHT = BORDER
