"""Pure helper functions (no GUI) - easy to test."""

import hashlib
import os
from datetime import datetime

from config import (MAX_NOTES, MAX_PLANT_ID, MAX_PLANT_NAME, MIN_PLANT_NAME, MIN_USERNAME,
                    PASSWORD_RULES, URGENT_WINDOW_DAYS)


def parse_date(value):
    return datetime.strptime(value, "%Y-%m-%d").date()


def effective_priority(base_priority, status, due, today):
    """Priority actually shown to the user.

    * completed tasks keep the priority they had
    * pending and past due           -> "Overdue"
    * pending Routine, due very soon -> "Urgent"  (automatic escalation)
    * everything else                -> the priority the user chose
    """
    if status == "Completed":
        return base_priority
    days_left = (due - today).days
    if days_left < 0:
        return "Overdue"
    if base_priority == "Routine" and days_left <= URGENT_WINDOW_DAYS:
        return "Urgent"
    return base_priority


def alert_stage(due, today):
    """Which reminder (if any) a pending task should trigger today."""
    days_left = (due - today).days
    if days_left < 0:
        return "overdue"
    if days_left == 0:
        return "today"
    if days_left <= URGENT_WINDOW_DAYS:
        return "soon"
    return None


def describe_due(due, today):
    days = (due - today).days
    if days < 0:
        n = -days
        return f"{n} day{'s' if n != 1 else ''} overdue"
    if days == 0:
        return "Today"
    if days == 1:
        return "Tomorrow"
    return f"In {days} days"


def hash_password(password, salt=None):
    salt = salt or os.urandom(16).hex()
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), bytes.fromhex(salt), 100_000
    ).hex()
    return salt, digest


# ----------------------------------------------------------------------------
# Validation: each function returns a message if the value is not allowed,
# otherwise None.
# ----------------------------------------------------------------------------
def username_problem(username):
    name = " ".join(username.split())
    if not name:
        return "Enter a username."
    if any(not (c.isalpha() or c == " ") for c in name):
        return "Letters only - no numbers or symbols."
    if sum(c.isalpha() for c in name) < MIN_USERNAME:
        return f"Use at least {MIN_USERNAME} letters."
    return None


def password_checks(password):
    """List of (label, passed) for every password rule."""
    return [(label, bool(rule(password))) for label, rule in PASSWORD_RULES]


def password_problem(password):
    missing = [label for label, ok in password_checks(password) if not ok]
    if missing:
        return "Password needs: " + ", ".join(missing) + "."
    return None


def plant_id_problem(plant_id):
    if not plant_id:
        return "Plant ID is required."
    if len(plant_id) > MAX_PLANT_ID:
        return f"Plant ID can be at most {MAX_PLANT_ID} characters."
    if not plant_id.isdigit() or not plant_id.isascii():
        return "Plant ID must be numbers only (0-9), e.g. 101."
    if len(plant_id) > 1 and plant_id.startswith("0"):
        return "Plant ID cannot start with 0 (use 7, not 007)."
    return None


def plant_name_problem(plant_name):
    if not plant_name:
        return "Plant Name is required."
    if len(plant_name) < MIN_PLANT_NAME:
        return f"Use at least {MIN_PLANT_NAME} characters."
    if len(plant_name) > MAX_PLANT_NAME:
        return f"Plant Name can be at most {MAX_PLANT_NAME} characters."
    if not any(c.isalpha() for c in plant_name):
        return "Plant Name must contain at least one letter."
    if any(not (c.isalnum() or c in " -'.()") for c in plant_name):
        return "Letters, numbers, spaces and - ' . ( ) only."
    return None


def due_date_problem(text, today, original=None):
    """`original` is the saved due date of a task being edited (it may stay in the past)."""
    try:
        due = parse_date(text)
    except ValueError:
        return "Due date must be a real date in YYYY-MM-DD format."
    if due < today and text != original:
        return "Due date cannot be in the past."
    return None


def notes_problem(notes):
    if len(notes) > MAX_NOTES:
        return f"Notes can be at most {MAX_NOTES} characters ({len(notes)} used)."
    return None