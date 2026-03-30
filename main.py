"""
main.py — CLI demo script for PawPal+.

Run with:  python main.py
"""

from datetime import datetime
from pawpal_system import Owner, Pet, Task, TaskType, Priority, Scheduler

# ---------------------------------------------------------------------------
# 1. Create an owner
# ---------------------------------------------------------------------------
jordan = Owner(name="Jordan", available_start="07:00", available_end="21:00")

# ---------------------------------------------------------------------------
# 2. Create two pets
# ---------------------------------------------------------------------------
mochi = Pet(name="Mochi", species="dog", age=3, breed="Shiba Inu")
luna  = Pet(name="Luna",  species="cat", age=5, breed="Domestic Shorthair")

jordan.add_pet(mochi)
jordan.add_pet(luna)

# ---------------------------------------------------------------------------
# 3. Add tasks (mix of fixed-time, flexible, and recurring)
# ---------------------------------------------------------------------------

# Mochi's tasks
mochi.add_task(Task(
    title="Morning walk",
    task_type=TaskType.WALK,
    duration_minutes=30,
    priority=Priority.HIGH,
    scheduled_time=datetime.today().replace(hour=7, minute=30, second=0, microsecond=0),
    notes="Leash required",
))

mochi.add_task(Task(
    title="Breakfast",
    task_type=TaskType.FEEDING,
    duration_minutes=10,
    priority=Priority.HIGH,
    is_recurring=True,
    recurrence_interval_hours=12,
))

mochi.add_task(Task(
    title="Evening walk",
    task_type=TaskType.WALK,
    duration_minutes=30,
    priority=Priority.MEDIUM,
    scheduled_time=datetime.today().replace(hour=18, minute=0, second=0, microsecond=0),
))

# Luna's tasks
luna.add_task(Task(
    title="Flea medication",
    task_type=TaskType.MEDICATION,
    duration_minutes=5,
    priority=Priority.HIGH,
    notes="Apply between shoulder blades",
))

luna.add_task(Task(
    title="Vet appointment",
    task_type=TaskType.APPOINTMENT,
    duration_minutes=60,
    priority=Priority.HIGH,
    scheduled_time=datetime.today().replace(hour=10, minute=0, second=0, microsecond=0),
))

luna.add_task(Task(
    title="Playtime",
    task_type=TaskType.PLAY,
    duration_minutes=20,
    priority=Priority.LOW,
))

# ---------------------------------------------------------------------------
# 4. Generate and print today's schedule
# ---------------------------------------------------------------------------
scheduler = Scheduler(jordan)
scheduler.generate_schedule()

print(scheduler.explain_plan())

print("\n--- All tasks (raw) ---")
header = f"{'Time':<8} {'Pet':<8} {'Task':<20} {'Type':<12} {'Priority':<8} {'Done'}"
print(header)
print("-" * len(header))
for entry in scheduler.get_schedule():
    t = entry.task
    print(
        f"{entry.start_time.strftime('%H:%M'):<8} "
        f"{entry.pet_name:<8} "
        f"{t.title:<20} "
        f"{t.task_type.value:<12} "
        f"{t.priority.value:<8} "
        f"{'done' if t.completed else '-'}"
    )
