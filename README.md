# 🌿 Plant Care Scheduler

A desktop app (Python + Tkinter + SQLite) that helps you plan and track plant care: watering, fertilizing, pruning and repotting. It reminds you when a task is due and shows your progress in a dashboard.

## Problem and solution

**Problem:** People forget when each plant was last watered or fertilized, so plants get over- or under-cared for.
**Solution:** Schedule care tasks per plant, get automatic priorities and reminders, repeat tasks daily or weekly, and see what is overdue at a glance.

## Features

* **Login / Create account** with live validation (letters-only username, strong password rules). Passwords are stored hashed (PBKDF2), never as plain text.
* **Dashboard:** stat cards, search and filters, task cards with priority and status, quick Done / Edit / Delete.
* **Add / Edit Task** with live input validation, a unique Plant ID rule, a calendar date picker and an optional plant photo.
* **Automatic priority:** a Routine task becomes Urgent one day before it is due; past-due tasks show as Overdue.
* **Repeating tasks:** Daily and Weekly tasks schedule their next task when completed.
* **Reminders:** pop-up and sound while the app is open.
* **Search** with filters and sorting, and a **Summary / Report** page with donut and bar charts and a completed-task history.
* **Profile photo:** upload, rotate and remove.

## Requirements

* Python 3.10 or newer, with Tkinter (included with the standard Python installer on Windows and macOS; on Linux install `python3-tk`)
* Pillow (see `requirements.txt`)

## Setup and run

```bash
git clone https://github.com/gyelmoo/Plant-Care-Scheduler.git
cd Plant-Care-Scheduler
pip install -r requirements.txt
python main.py
```

The database (`plant_care.db`) is created automatically on first run. Create an account on the login screen to begin.

## Project structure

|File / folder|Purpose|
|-|-|
|`main.py`|Starts the app|
|`app.py`|Main window, sidebar and navigation|
|`login\_view.py`|Login and create-account screen|
|`dashboard\_view.py`|Home dashboard|
|`task\_form\_view.py`|Add / Edit task form and validation|
|`search\_view.py`|Search page|
|`summary\_view.py`|Summary / Report page|
|`profile\_view.py`|Profile photo window|
|`reminders.py`|Reminder checks, pop-up and sound|
|`database.py`|SQLite database layer|
|`helpers.py`|Logic and validation rules (no GUI code)|
|`config.py`|Settings, limits and colours|
|`theme.py`, `ui.py`, `widgets.py`|Fonts, icons, rounded widgets, date picker|
|`plant\_photos.py`|Saving and removing plant pictures|
|`assets/`|Decorative images|
|`REDESIGN\_NOTES.md`|Notes on the redesign and validation|

## Settings

Limits and options (password rules, field lengths, reminder interval, `ONE\_TASK\_PER\_PLANT\_ID`) are in `config.py`.

## 

