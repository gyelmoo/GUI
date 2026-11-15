"""Settings, constants and colours used by the whole app."""

import os
import string

# ----------------------------------------------------------------------------
# Settings you can change
# ----------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "plant_care.db")
AVATAR_DIR = os.path.join(BASE_DIR, "avatars")
AVATAR_SAVE_SIZE = 400        # saved profile pictures are 400 x 400 px
AVATAR_MAX_MB = 5             # biggest picture file accepted
AVATAR_EXTENSIONS = (".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp")
PLANT_PHOTO_DIR = os.path.join(BASE_DIR, "plant_photos")
PLANT_PHOTO_MAX_MB = 8          # biggest plant picture accepted
PLANT_PHOTO_SIZE = 800          # saved plant pictures fit inside 800 x 800 px
PLANT_PHOTO_EXTENSIONS = (".png", ".jpg", ".jpeg")

PRIORITIES = ["Urgent", "Routine", "Optional"]
TASK_TYPES = ["Watering", "Fertilizing", "Pruning", "Repotting", "Other"]
REPEATS = ["One-time", "Daily", "Weekly"]
REPEAT_DAYS = {"Daily": 1, "Weekly": 7}
TASK_ICONS = {"Watering": "💧", "Fertilizing": "🧪", "Pruning": "✂️",
              "Repotting": "🪴", "Other": "🌿"}

URGENT_WINDOW_DAYS = 1        # Routine becomes Urgent this many days before the due date
CHECK_INTERVAL_MS = 60_000    # reminder check every 60 seconds while the app is open

# --- Input limits (validation) ----------------------------------------------
MIN_USERNAME = 3
MAX_USERNAME = 30
MAX_PASSWORD = 64
MAX_PLANT_ID = 6           # Plant IDs are numbers only, up to 6 digits
MIN_PLANT_NAME = 2
MAX_PLANT_NAME = 50
MAX_NOTES = 200
MAX_SEARCH = 50

# Plant IDs must be unique: two active (pending) tasks can never share a Plant ID.
# (A Daily/Weekly task keeps its ID when it reschedules itself - the finished one is
# history.) Set this to False to allow several tasks for the same plant under one ID.
ONE_TASK_PER_PLANT_ID = True

PASSWORD_RULES = [            # (label shown to the user, test)
    ("8+ characters", lambda p: len(p) >= 8),
    ("1 uppercase letter", lambda p: any(c.isupper() for c in p)),
    ("1 number", lambda p: any(c.isdigit() for c in p)),
    ("1 special character (!@#$...)", lambda p: any(c in string.punctuation for c in p)),
]

# ----------------------------------------------------------------------------
# Colours
# ----------------------------------------------------------------------------
# Botanical palette
CREAM = "#fbf7ec"          # warm cream page background
IVORY = "#fffdf7"          # cards
DARK = "#1f4d36"           # deep forest green: sidebar, primary buttons
MID = "#2b5d43"            # hover for forest green
SAGE = "#6fa75a"           # sage green: active navigation, highlights
SAGE_LIGHT = "#e6f1dc"     # pale sage: soft fills
PINK = "#f4b6bf"           # pastel pink accents
PINK_SOFT = "#fde7e5"
YELLOW_SOFT = "#fff1cf"
MINT_SOFT = "#e8f2df"
FIELD_BORDER = "#d8dccb"

BG = CREAM
WHITE = "#ffffff"
ACCENT = "#b9de7e"         # light lime (text on the dark sidebar)
TEXT = "#1f3a2b"
MUTED = "#687a6e"
GOOD = "#3f8a4f"
BAD = "#c0392b"
WARN = "#b07d1a"
BORDER = "#ebe4d2"

# ----------------------------------------------------------------------------
# Table columns and tag colours (used by Search and Summary)
# ----------------------------------------------------------------------------
COLUMNS = {
    "plant_id": ("Plant ID", 80, "center"),
    "plant_name": ("Plant Name", 150, "w"),
    "task_type": ("Task Type", 90, "w"),
    "due_date": ("Due Date", 95, "center"),
    "due_in": ("Due", 105, "center"),
    "priority": ("Priority", 80, "center"),
    "repeat": ("Repeat", 80, "center"),
    "status": ("Status", 85, "center"),
    "completed_on": ("Completed On", 105, "center"),
    "notes": ("Notes", 240, "w"),
}

TAG_COLORS = {
    "urgent": ("#a93226", "#fdecea"),
    "overdue": ("#7b1e1e", "#f5c6cb"),
    "routine": ("#1e6b3a", "#eaf4ec"),
    "optional": ("#8a6414", "#fdf3dc"),
    "done": ("#4f6b58", WHITE),
}

# Pill colours used on the dashboard (text colour, fill colour)
PILL = {
    "urgent": ("#a93226", "#fbdcdc"),
    "overdue": ("#7b1e1e", "#f5c6cb"),
    "routine": ("#8a6414", "#fdeab8"),
    "optional": ("#2f6f4a", "#dcebd9"),
    "pending": ("#2f6f4a", "#dcebd9"),
    "completed": ("#62756a", "#e8ece9"),
}