"""Profile picture: avatar drawing and the "My Profile" window."""

import os
import tkinter as tk
from tkinter import filedialog, messagebox

from config import (ACCENT, AVATAR_DIR, AVATAR_EXTENSIONS, AVATAR_MAX_MB, AVATAR_SAVE_SIZE,
                    DARK, GOOD, MUTED, TEXT, WARN, WHITE)
import theme
from widgets import PIL_OK, disc_mask

if PIL_OK:
    from PIL import Image, ImageOps, ImageTk


class ProfileMixin:
    def circle_avatar_image(self, size, bg, picture_override=None):
        """Smooth round avatar with a light-green ring: the photo, or a plain pink disc.

        `picture_override` is an unsaved PIL image to preview instead of the saved photo.
        Returns (PhotoImage, has_photo) or None if Pillow is not available.
        """
        if not PIL_OK:
            return None
        try:
            ring = max(2, size // 40)
            inner = size - 2 * ring
            base = Image.new("RGB", (size, size), bg)
            base.paste(Image.new("RGB", (size, size), ACCENT), (0, 0), disc_mask(size))

            picture, has_photo = None, False
            if picture_override is not None:
                picture = ImageOps.fit(picture_override.convert("RGB"), (inner, inner),
                                       Image.LANCZOS)
                has_photo = True
            elif self.user and self.user.get("avatar"):
                path = os.path.join(AVATAR_DIR, self.user["avatar"])
                if os.path.exists(path):
                    with Image.open(path) as src:
                        picture = ImageOps.fit(src.convert("RGB"), (inner, inner),
                                               Image.LANCZOS)
                    has_photo = True
            if picture is None:
                picture = Image.new("RGB", (inner, inner), "#f6d3d8")
            base.paste(picture, (ring, ring), disc_mask(inner))
            return ImageTk.PhotoImage(base), has_photo
        except Exception:
            return None

    def avatar_widget(self, parent, size, bg, command=None, picture=None):
        """Circular avatar: the user's photo, or a pink circle with their initial."""
        canvas = tk.Canvas(parent, width=size, height=size, bg=bg, highlightthickness=0,
                           cursor="hand2" if command else "")
        initial = (self.user["username"][:1] if self.user else "?").upper()
        result = self.circle_avatar_image(size, bg, picture)
        if result is not None:
            photo, has_photo = result
            canvas.photo = photo                      # keep a reference or Tk drops it
            canvas.create_image(size / 2, size / 2, image=photo)
        else:                                         # Pillow missing: simple fallback
            has_photo = False
            canvas.create_oval(2, 2, size - 2, size - 2, fill="#f6d3d8", outline=ACCENT,
                               width=2)
        if not has_photo:
            canvas.create_text(size / 2, size / 2, text=initial, fill=DARK,
                               font=("Helvetica", max(10, int(size * 0.4)), "bold"))
        if command:
            canvas.bind("<Button-1>", lambda e: command())
        return canvas

    def build_sidebar_avatar(self):
        holder = self.sidebar_avatar_holder
        if holder is None or not holder.winfo_exists():
            return
        for child in holder.winfo_children():
            child.destroy()
        if self.user and self.user.get("avatar"):
            self.avatar_widget(holder, 88, DARK, command=self.open_profile).pack()
            return
        # No profile photo yet: show the app's leaf logo (click it to add a photo)
        logo = theme.asset("logo_light", 92, 92)
        if logo is None:
            self.avatar_widget(holder, 84, DARK, command=self.open_profile).pack()
            return
        lbl = tk.Label(holder, image=logo, bg=DARK, bd=0, cursor="hand2")
        lbl.image = logo
        lbl.pack()
        lbl.bind("<Button-1>", lambda e: self.open_profile())

    def read_avatar_file(self, path):
        """Open any image file and return a square AVATAR_SAVE_SIZE picture (not saved yet)."""
        with Image.open(path) as src:
            img = ImageOps.exif_transpose(src).convert("RGB")
        return ImageOps.fit(img, (AVATAR_SAVE_SIZE, AVATAR_SAVE_SIZE), Image.LANCZOS)

    def saved_avatar_image(self):
        """The currently saved profile picture as a PIL image, or None."""
        if not self.user.get("avatar"):
            return None
        path = os.path.join(AVATAR_DIR, self.user["avatar"])
        if not os.path.exists(path):
            return None
        with Image.open(path) as src:
            return src.convert("RGB")

    def store_avatar(self, img):
        """Write the picture to /avatars and remember it in the database."""
        os.makedirs(AVATAR_DIR, exist_ok=True)
        name = f"user_{self.user['id']}.png"
        img.save(os.path.join(AVATAR_DIR, name))
        self.db.set_avatar(self.user["id"], name)
        self.user["avatar"] = name

    def remove_avatar(self):
        if self.user.get("avatar"):
            path = os.path.join(AVATAR_DIR, self.user["avatar"])
            if os.path.exists(path):
                os.remove(path)
        self.db.set_avatar(self.user["id"], None)
        self.user["avatar"] = None

    def open_profile(self):
        if self.profile_win is not None and self.profile_win.winfo_exists():
            self.profile_win.lift()
            return
        win = tk.Toplevel(self)
        self.profile_win = win
        win.title("My Profile")
        win.configure(bg=WHITE)
        win.resizable(False, False)
        win.transient(self)

        pending = {"img": None}          # a chosen / rotated picture that is not saved yet

        tk.Label(win, text="🌿  My Profile", bg=DARK, fg=ACCENT, anchor="w",
                 font=("Helvetica", 13, "bold"), padx=18, pady=12).pack(fill="x")
        body = tk.Frame(win, bg=WHITE, padx=40, pady=20)
        body.pack(fill="both", expand=True)
        tk.Frame(body, width=300, height=1, bg=WHITE).pack()     # keeps the window a sensible width

        preview = tk.Frame(body, bg=WHITE)
        preview.pack()
        tk.Label(body, text=self.user["username"], bg=WHITE, fg=TEXT,
                 font=("Helvetica", 13, "bold")).pack(pady=(10, 2))
        note = tk.Label(body, text="", bg=WHITE, fg=MUTED, font=("Helvetica", 9),
                        wraplength=260, justify="center")
        note.pack(pady=(0, 10))

        buttons = tk.Frame(body, bg=WHITE)
        buttons.pack(fill="x")

        def has_saved():
            return bool(self.user.get("avatar"))

        def redraw():
            for child in preview.winfo_children():
                child.destroy()
            self.avatar_widget(preview, 150, WHITE, picture=pending["img"]).pack()
            has_pending = pending["img"] is not None
            shown = has_pending or has_saved()
            upload_btn.config(text="Change photo" if shown else "Upload photo")
            rotate_btn.config(state="normal" if (shown and PIL_OK) else "disabled")
            save_btn.config(state="normal" if has_pending else "disabled",
                            bg="#5d9d69" if has_pending else "#c9d6cd")
            can_remove = shown
            remove_btn.config(state="normal" if can_remove else "disabled")
            self.build_sidebar_avatar()

        def do_upload():
            path = filedialog.askopenfilename(
                parent=win, title="Choose a profile picture",
                filetypes=[("Images", "*.png *.jpg *.jpeg *.gif *.bmp *.webp"),
                           ("All files", "*.*")])
            if not path:
                return
            # --- validation: file type and size -------------------------------
            if not path.lower().endswith(AVATAR_EXTENSIONS):
                messagebox.showerror("Wrong file type",
                                     "Please choose an image file (PNG, JPG, GIF, BMP or WEBP).",
                                     parent=win)
                return
            try:
                too_big = os.path.getsize(path) > AVATAR_MAX_MB * 1024 * 1024
            except OSError:
                too_big = False
            if too_big:
                messagebox.showerror("Image too large",
                                     f"Please choose a picture smaller than {AVATAR_MAX_MB} MB.",
                                     parent=win)
                return
            try:
                pending["img"] = self.read_avatar_file(path)
            except Exception:
                messagebox.showerror("Could not use this image",
                                     "That file could not be opened as an image. "
                                     "Try a PNG or JPG.", parent=win)
                return
            note.config(text="Preview only - press Save photo to keep it.", fg=WARN)
            redraw()

        def do_rotate():
            try:
                base = pending["img"] or self.saved_avatar_image()
                pending["img"] = base.rotate(-90, expand=True)
            except Exception:
                messagebox.showerror("Rotate failed", "The photo could not be rotated.",
                                     parent=win)
                return
            note.config(text="Preview only - press Save photo to keep it.", fg=WARN)
            redraw()

        def do_save():
            if pending["img"] is None:
                return
            try:
                self.store_avatar(pending["img"])
            except Exception:
                messagebox.showerror("Could not save", "The photo could not be saved.",
                                     parent=win)
                return
            pending["img"] = None
            note.config(text="Profile photo saved.", fg=GOOD)
            redraw()

        def do_remove():
            if not has_saved():                       # only an unsaved preview: just discard it
                pending["img"] = None
                note.config(text="Unsaved photo discarded.", fg=MUTED)
                redraw()
                return
            if messagebox.askyesno("Remove photo", "Remove your profile photo?", parent=win):
                pending["img"] = None
                self.remove_avatar()
                note.config(text="Profile photo removed.", fg=MUTED)
                redraw()

        def do_close():
            if pending["img"] is not None and not messagebox.askyesno(
                    "Unsaved photo", "You have a photo that is not saved. Close without "
                    "saving?", parent=win):
                return
            win.destroy()

        upload_btn = tk.Button(buttons, text="Upload photo", command=do_upload, bg=DARK,
                               fg=WHITE, activebackground="#143425", activeforeground=WHITE,
                               relief="flat", font=("Helvetica", 10, "bold"), padx=12, pady=7,
                               cursor="hand2")
        upload_btn.pack(fill="x", pady=(0, 6))
        rotate_btn = tk.Button(buttons, text="Rotate 90°", command=do_rotate, bg=WHITE, fg=TEXT,
                               activebackground="#eef2ef", relief="solid", bd=1,
                               font=("Helvetica", 10, "bold"), padx=12, pady=6, cursor="hand2",
                               disabledforeground="#a9b8ae")
        rotate_btn.pack(fill="x", pady=(0, 6))
        save_btn = tk.Button(buttons, text="Save photo", command=do_save, bg="#c9d6cd",
                             fg=WHITE, activebackground="#4c8758", activeforeground=WHITE,
                             relief="flat", font=("Helvetica", 10, "bold"), padx=12, pady=7,
                             cursor="hand2", disabledforeground=WHITE)
        save_btn.pack(fill="x", pady=(0, 6))
        remove_btn = tk.Button(buttons, text="Remove photo", command=do_remove, bg="#e27667",
                               fg=WHITE, activebackground="#cc6153", activeforeground=WHITE,
                               relief="flat", font=("Helvetica", 10, "bold"), padx=12, pady=7,
                               cursor="hand2", disabledforeground="#f7d8d3")
        remove_btn.pack(fill="x", pady=(0, 6))
        tk.Button(buttons, text="Close", command=do_close, bg=WHITE, fg=MUTED,
                  relief="flat", cursor="hand2", font=("Helvetica", 10)).pack(pady=(4, 0))
        win.protocol("WM_DELETE_WINDOW", do_close)

        if not PIL_OK:
            upload_btn.config(state="disabled", bg="#a9b8ae")
            note.config(text="Photo upload needs the Pillow library.\n"
                             "Run:  pip install pillow   then restart the app.", fg=WARN)
        redraw()

        # centre the dialog over the main window, whatever size the content needs
        win.update_idletasks()
        w, h = win.winfo_reqwidth(), win.winfo_reqheight()
        x = self.winfo_rootx() + max(0, (self.winfo_width() - w) // 2)
        y = self.winfo_rooty() + max(0, (self.winfo_height() - h) // 2)
        win.geometry(f"+{x}+{y}")
