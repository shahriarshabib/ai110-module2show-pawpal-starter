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

## Testing PawPal+

### Run the tests

```bash
python -m pytest
```

### What the tests cover

| Category | Tests | What is verified |
|---|---|---|
| `Task` lifecycle | 6 | `mark_complete()`, `is_overdue()`, `to_dict()` |
| `Pet` management | 6 | `add_task()`, `remove_task()`, `get_tasks_by_priority()`, duplicate guard |
| `Owner` management | 4 | `add_pet()`, `remove_pet()`, `get_all_tasks()`, `available_minutes()` |
| Scheduler — schedule generation | 4 | Returns entries, respects priority, skips tasks that don't fit, exactly-fills-window |
| Scheduler — sort by time | 2 | Ascending order, unscheduled tasks last |
| Scheduler — filter | 3 | By pet name, by completion, combined AND filters |
| Recurring tasks | 3 | Auto-spawn on completion, no spawn for one-off, correct time offset |
| Conflict detection | 3 | Overlap found, no overlap, exact same start time |
| Edge cases | 9 | Empty owner/pet, filter with no results, explain before generate, bad IDs, task that exactly fills window, recurring with no base time |

**Total: 40 tests — 40 passing**

### Confidence level

★★★★☆ (4/5)

The core scheduling logic (priority ordering, window fitting, recurring tasks, conflict detection) is thoroughly tested including edge cases. The one gap is integration with Streamlit session state — those code paths are not covered by automated tests and would need manual or browser-based testing.

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
