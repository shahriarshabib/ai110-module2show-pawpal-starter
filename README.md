# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Smarter Scheduling

PawPal+ goes beyond a simple to-do list with four algorithmic features:

| Feature | How it works |
|---|---|
| **Sort by time** | `Scheduler.sort_by_time()` orders tasks by `scheduled_time` ascending using a `lambda` key; tasks with no fixed time are sorted to the end. |
| **Filter tasks** | `Scheduler.filter_tasks()` accepts any combination of `pet_name`, `completed`, `task_type`, and `priority` keyword arguments and applies them with AND logic. |
| **Recurring task auto-spawn** | When `Pet.complete_task(id)` is called, it calls `Task.mark_complete()`. If the task is recurring, `mark_complete()` returns a new `Task` with `scheduled_time = original + recurrence_interval_hours`; the pet's task list is updated automatically. |
| **Conflict detection** | After placing all tasks, `Scheduler.detect_conflicts()` scans `ScheduleEntry` windows for overlaps and returns warning pairs. Conflicts are displayed in the UI and CLI rather than silently dropping tasks. |

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.
