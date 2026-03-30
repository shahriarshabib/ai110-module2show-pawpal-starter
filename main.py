"""
main.py - CLI demo for PawPal+ algorithmic features.

Demonstrates:
  1. Sorting tasks by time (tasks added intentionally out of order)
  2. Filtering tasks by pet name and completion status
  3. Recurring task auto-spawn on completion
  4. Conflict detection with a deliberate overlap

Run with:  python main.py
"""

from datetime import datetime
from pawpal_system import Owner, Pet, Task, TaskType, Priority, Scheduler

SEP = "-" * 60


def section(title: str) -> None:
    print(f"\n{SEP}\n{title}\n{SEP}")


# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------
jordan = Owner(name="Jordan", available_start="07:00", available_end="21:00")

mochi = Pet(name="Mochi", species="dog", age=3, breed="Shiba Inu")
luna  = Pet(name="Luna",  species="cat", age=5, breed="Domestic Shorthair")
jordan.add_pet(mochi)
jordan.add_pet(luna)

today = datetime.today().replace(second=0, microsecond=0)

# Add tasks deliberately OUT OF time order to show sorting
mochi.add_task(Task("Evening walk",   TaskType.WALK,     30, Priority.MEDIUM,
                    scheduled_time=today.replace(hour=18, minute=0)))
mochi.add_task(Task("Breakfast",      TaskType.FEEDING,  10, Priority.HIGH,
                    is_recurring=True, recurrence_interval_hours=12))
mochi.add_task(Task("Morning walk",   TaskType.WALK,     30, Priority.HIGH,
                    scheduled_time=today.replace(hour=7, minute=30)))

luna.add_task(Task("Flea medication", TaskType.MEDICATION, 5, Priority.HIGH,
                   notes="Apply between shoulder blades"))
luna.add_task(Task("Playtime",        TaskType.PLAY,     20, Priority.LOW))
luna.add_task(Task("Vet appointment", TaskType.APPOINTMENT, 60, Priority.HIGH,
                   scheduled_time=today.replace(hour=10, minute=0)))

# Deliberate conflict: Luna's grooming overlaps with vet appointment (10:00-11:00)
luna.add_task(Task("Grooming",        TaskType.GROOMING, 45, Priority.MEDIUM,
                   scheduled_time=today.replace(hour=10, minute=30)))

scheduler = Scheduler(jordan)
all_tasks = jordan.get_all_tasks()

# ---------------------------------------------------------------------------
# 1. Sort by time
# ---------------------------------------------------------------------------
section("1. Tasks sorted by scheduled_time (unscheduled tasks go last)")
sorted_by_time = scheduler.sort_by_time(all_tasks)
fmt = "  {:<22} {:<8} {:<10} {}"
print(fmt.format("Task", "Pet", "Priority", "Time"))
print("  " + "-" * 52)
for t in sorted_by_time:
    time_str = t.scheduled_time.strftime("%H:%M") if t.scheduled_time else "(flexible)"
    print(fmt.format(t.title, t.pet_name, t.priority.value, time_str))

# ---------------------------------------------------------------------------
# 2. Filter tasks
# ---------------------------------------------------------------------------
section("2a. Filter - only Mochi's tasks")
mochi_tasks = scheduler.filter_tasks(all_tasks, pet_name="Mochi")
for t in mochi_tasks:
    print(f"  [{t.priority.value}] {t.title}")

section("2b. Filter - incomplete HIGH-priority tasks across all pets")
urgent = scheduler.filter_tasks(all_tasks, completed=False, priority=Priority.HIGH)
for t in urgent:
    print(f"  {t.pet_name:<8} {t.title}")

# ---------------------------------------------------------------------------
# 3. Recurring task auto-spawn
# ---------------------------------------------------------------------------
section("3. Recurring task: complete Mochi's Breakfast -> auto-spawn next")
breakfast = next(t for t in mochi.tasks if t.title == "Breakfast")
print(f"  Before: {len(mochi.tasks)} tasks, Breakfast completed={breakfast.completed}")

mochi.complete_task(breakfast.id)   # marks done + appends next occurrence

print(f"  After:  {len(mochi.tasks)} tasks, Breakfast completed={breakfast.completed}")
spawned = mochi.tasks[-1]
print(f"  Spawned: '{spawned.title}' scheduled for "
      f"{spawned.scheduled_time.strftime('%H:%M') if spawned.scheduled_time else 'TBD'}")

section("2c. Filter - completed tasks (should now include Breakfast)")
done = scheduler.filter_tasks(jordan.get_all_tasks(), completed=True)
for t in done:
    print(f"  {t.pet_name:<8} {t.title}")

# ---------------------------------------------------------------------------
# 4. Full schedule + conflict detection
# ---------------------------------------------------------------------------
section("4. Full schedule with conflict detection")
scheduler.generate_schedule()
print(scheduler.explain_plan())
