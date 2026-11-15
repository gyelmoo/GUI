# Plant Care Scheduler: redesign notes

## How to run
1. Install Pillow once: `pip install pillow`. It is needed for the rounded design, the icons and the plant pictures.
2. Run `python main.py`.

Your existing `plant_care.db` keeps working. On the first start, a `photo` column is added to the `plants` table automatically, the same way the `avatar` column was added before.

## New files
| File | What it does |
|---|---|
| `theme.py` | Fonts, drawn icons, rounded shapes, donut/ring charts and loading of the decorative pictures |
| `ui.py` | Reusable rounded widgets: `RoundBox` (cards), `RoundButton`, `IconButton`, `Pill`, input fields, `RoundProgress`, `PageHeader` |
| `plant_photos.py` | Checks, saves, replaces and removes plant pictures (stored in `plant_photos/`) |
| `assets/` | Plant illustrations cut from our two sticker sheets (transparent PNGs) |

## What changed on each screen
- **All screens:** cream background, deep-green sidebar with rounded sage highlight, drawn icons, rounded cards with soft shadows and Segoe UI / Georgia fonts. The highlight now always matches the open screen, so Summary/Report is highlighted on the Summary/Report screen.
- **Login:** the green welcome panel has a curved edge, the "Grow with care." heading, feature chips and plant illustrations. The sign-in card has rounded fields. Validation works as before, and the account button still turns green when the username and password are valid.
- **Dashboard:** greeting, date chip, reminder bell, Add Task, four stat cards, search and filters, task cards and an illustrated empty state. The Plant Care Tip card also shows the progress bar.
- **Add Task / Edit Task:** all the old fields and validation are kept. The new **Upload Plant Picture** panel has a preview and lets you replace or remove the picture. There is one picture per plant, shared by all of that plant's tasks.
- **Search:** task cards show the **user's own uploaded picture**. If a plant has no picture, the card shows a neutral "No photo" tile, never a stock picture. Filters: Plant Type, Status and Priority. You can sort by Due Date, Plant Name, Priority or Task Type. The ⋮ menu marks a task completed, edits it or deletes it, and double-clicking a card edits it.
- **Summary / Report:** stat cards, overall progress, donut chart, bar chart, tip card and the Completed Task History table, which keeps all 8 columns. A period selector offers All Time (the default), This Month and This Week.
  - The bar chart now shows **Urgent / Routine / Optional** only. Overdue is a status, so an overdue task is counted under the priority it was given, and the Overdue count appears as its own badge.

## Unchanged logic
- Login and registration rules
- Unique Plant ID rule
- Automatic Routine → Urgent escalation
- Overdue detection
- Daily/Weekly rescheduling
- Reminder pop-ups and sounds
- Profile photo
- Date picker

## Note on the buttons
Plain `tk.Button` widgets are always square. The rounded buttons are drawn on a `Canvas` (see `RoundButton` in `ui.py`) and react to hover and click like normal buttons.

## Live input validation (update 2)
Every input now gives feedback while you type or choose:

| Input | Feedback |
|---|---|
| Username (login) | Letters-only check, minimum length, and whether the name already has an account ("Account found") or is free ("you can create a new account") |
| Password (login) | Lists the rules a new account still needs, or shows "✓ Strong password" |
| Plant ID | Allowed characters, and **unique**: an ID already used by another pending task is refused, with that task named. Upper/lower case counts as the same (P1 = p1). |
| Plant Name | Required, length and allowed characters |
| Task Type / Priority / Repeat | Confirms the choice and explains what it does |
| Due Date | Shows how far away it is (e.g. "Tomorrow - Sun, 15 Nov 2026"); past dates are refused |
| Notes | Character counter that turns orange near the 200-character limit and red past it |
| Plant picture | File type and size check, with a note that it is saved when you press Save |
| Save Task button | Muted until every field is valid, then solid green. A line above it says what is still missing. |
| Search box | Results update as you type |

A Daily/Weekly task keeps its Plant ID when it reschedules itself, because the finished task is history. To allow several pending tasks per Plant ID again, set `ONE_TASK_PER_PLANT_ID = False` in `config.py`.
