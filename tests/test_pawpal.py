"""
tests/test_pawpal.py — Automated tests for PawPal+ backend logic.

Run with:  python -m pytest
"""

from datetime import datetime
import pytest
from pawpal_system import (
    Owner, Pet, Task, TaskType, Priority, Scheduler, ScheduleEntry
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_task(title="Walk", task_type=TaskType.WALK, duration=20,
              priority=Priority.MEDIUM, scheduled_time=None):
    return Task(title=title, task_type=task_type, duration_minutes=duration,
                priority=priority, scheduled_time=scheduled_time)


def make_pet(name="Mochi", species="dog"):
    return Pet(name=name, species=species, age=2)


# ---------------------------------------------------------------------------
# Task tests
# ---------------------------------------------------------------------------

def test_mark_complete_changes_status():
    """Calling mark_complete() should set completed to True."""
    task = make_task()
    assert task.completed is False
    task.mark_complete()
    assert task.completed is True


def test_mark_complete_idempotent():
    """Calling mark_complete() twice should leave completed as True."""
    task = make_task()
    task.mark_complete()
    task.mark_complete()
    assert task.completed is True


def test_is_overdue_returns_false_when_no_scheduled_time():
    """A task with no scheduled_time is never overdue."""
    task = make_task()
    assert task.is_overdue() is False


def test_is_overdue_returns_true_for_past_time():
    """A task scheduled in the past (and not completed) is overdue."""
    past = datetime(2000, 1, 1, 9, 0)
    task = make_task(scheduled_time=past)
    assert task.is_overdue() is True


def test_is_overdue_returns_false_when_completed():
    """A completed task is never considered overdue."""
    past = datetime(2000, 1, 1, 9, 0)
    task = make_task(scheduled_time=past)
    task.mark_complete()
    assert task.is_overdue() is False


def test_to_dict_contains_expected_keys():
    """to_dict() should include title, type, priority, and pet keys."""
    task = make_task(title="Breakfast", task_type=TaskType.FEEDING)
    d = task.to_dict()
    for key in ("title", "type", "priority", "pet", "completed"):
        assert key in d


# ---------------------------------------------------------------------------
# Pet tests
# ---------------------------------------------------------------------------

def test_add_task_increases_task_count():
    """Adding a task to a pet should increase its task count by 1."""
    pet = make_pet()
    assert len(pet.tasks) == 0
    pet.add_task(make_task())
    assert len(pet.tasks) == 1


def test_add_task_stamps_pet_name():
    """add_task() should set task.pet_name to the pet's name."""
    pet = make_pet(name="Luna")
    task = make_task()
    pet.add_task(task)
    assert task.pet_name == "Luna"


def test_add_multiple_tasks():
    """Adding three tasks should result in task count of 3."""
    pet = make_pet()
    for title in ("Walk", "Feed", "Groom"):
        pet.add_task(make_task(title=title))
    assert len(pet.tasks) == 3


def test_remove_task_by_id_succeeds():
    """remove_task() with a valid id should return True and shrink task list."""
    pet = make_pet()
    task = make_task()
    pet.add_task(task)
    result = pet.remove_task(task.id)
    assert result is True
    assert len(pet.tasks) == 0


def test_remove_task_with_bad_id_returns_false():
    """remove_task() with an unknown id should return False."""
    pet = make_pet()
    pet.add_task(make_task())
    assert pet.remove_task("nonexistent-id") is False


def test_get_tasks_by_priority_filters_correctly():
    """get_tasks_by_priority() should return only tasks with the given priority."""
    pet = make_pet()
    pet.add_task(make_task(priority=Priority.HIGH))
    pet.add_task(make_task(priority=Priority.LOW))
    high = pet.get_tasks_by_priority(Priority.HIGH)
    assert len(high) == 1
    assert high[0].priority == Priority.HIGH


# ---------------------------------------------------------------------------
# Owner tests
# ---------------------------------------------------------------------------

def test_add_pet_increases_count():
    """add_pet() should register the pet."""
    owner = Owner("Jordan")
    owner.add_pet(make_pet())
    assert len(owner.pets) == 1


def test_add_duplicate_pet_ignored():
    """Adding a pet with the same name twice should not create a duplicate."""
    owner = Owner("Jordan")
    owner.add_pet(make_pet(name="Mochi"))
    owner.add_pet(make_pet(name="Mochi"))
    assert len(owner.pets) == 1


def test_get_all_tasks_aggregates_across_pets():
    """get_all_tasks() should return tasks from all pets combined."""
    owner = Owner("Jordan")
    dog = make_pet("Mochi")
    cat = make_pet("Luna", species="cat")
    dog.add_task(make_task("Walk"))
    dog.add_task(make_task("Feed"))
    cat.add_task(make_task("Play"))
    owner.add_pet(dog)
    owner.add_pet(cat)
    assert len(owner.get_all_tasks()) == 3


def test_available_minutes_calculation():
    """available_minutes() should return correct window length in minutes."""
    owner = Owner("Jordan", available_start="08:00", available_end="20:00")
    assert owner.available_minutes() == 720


# ---------------------------------------------------------------------------
# Scheduler tests
# ---------------------------------------------------------------------------

def test_generate_schedule_returns_entries():
    """generate_schedule() should return at least one ScheduleEntry."""
    owner = Owner("Jordan", available_start="08:00", available_end="20:00")
    pet = make_pet()
    pet.add_task(make_task("Walk", duration=30))
    owner.add_pet(pet)
    scheduler = Scheduler(owner)
    schedule = scheduler.generate_schedule()
    assert len(schedule) >= 1
    assert isinstance(schedule[0], ScheduleEntry)


def test_schedule_respects_priority_order():
    """High-priority flexible tasks should be placed before low-priority ones."""
    owner = Owner("Jordan", available_start="08:00", available_end="20:00")
    pet = make_pet()
    pet.add_task(make_task("Low task",  priority=Priority.LOW,  duration=10))
    pet.add_task(make_task("High task", priority=Priority.HIGH, duration=10))
    owner.add_pet(pet)
    schedule = Scheduler(owner).generate_schedule()
    titles = [e.task.title for e in schedule]
    assert titles.index("High task") < titles.index("Low task")


def test_schedule_skips_tasks_that_exceed_window():
    """A task too long to fit in the window should not appear in the schedule."""
    owner = Owner("Jordan", available_start="08:00", available_end="08:05")
    pet = make_pet()
    pet.add_task(make_task("Long task", duration=60))
    owner.add_pet(pet)
    schedule = Scheduler(owner).generate_schedule()
    assert len(schedule) == 0


def test_explain_plan_contains_task_title():
    """explain_plan() output should mention every scheduled task's title."""
    owner = Owner("Jordan", available_start="08:00", available_end="20:00")
    pet = make_pet()
    pet.add_task(make_task("Morning walk"))
    owner.add_pet(pet)
    scheduler = Scheduler(owner)
    scheduler.generate_schedule()
    explanation = scheduler.explain_plan()
    assert "Morning walk" in explanation


# ---------------------------------------------------------------------------
# sort_by_time tests
# ---------------------------------------------------------------------------

def test_sort_by_time_orders_ascending():
    """Tasks with earlier scheduled_time should appear first."""
    owner = Owner("Jordan")
    scheduler = Scheduler(owner)
    today = datetime.today().replace(second=0, microsecond=0)
    late  = make_task("Late",  scheduled_time=today.replace(hour=18))
    early = make_task("Early", scheduled_time=today.replace(hour=7))
    mid   = make_task("Mid",   scheduled_time=today.replace(hour=12))
    result = scheduler.sort_by_time([late, early, mid])
    assert [t.title for t in result] == ["Early", "Mid", "Late"]


def test_sort_by_time_unscheduled_tasks_go_last():
    """Tasks with no scheduled_time should appear after fixed-time tasks."""
    owner = Owner("Jordan")
    scheduler = Scheduler(owner)
    today = datetime.today().replace(second=0, microsecond=0)
    fixed = make_task("Fixed", scheduled_time=today.replace(hour=9))
    flex  = make_task("Flex")
    result = scheduler.sort_by_time([flex, fixed])
    assert result[0].title == "Fixed"
    assert result[1].title == "Flex"


# ---------------------------------------------------------------------------
# filter_tasks tests
# ---------------------------------------------------------------------------

def test_filter_by_pet_name():
    """filter_tasks(pet_name=) should return only that pet's tasks."""
    owner = Owner("Jordan")
    scheduler = Scheduler(owner)
    dog = make_pet("Mochi")
    cat = make_pet("Luna", species="cat")
    t1 = make_task("Walk"); t1.pet_name = "Mochi"
    t2 = make_task("Play"); t2.pet_name = "Luna"
    result = scheduler.filter_tasks([t1, t2], pet_name="Mochi")
    assert len(result) == 1
    assert result[0].pet_name == "Mochi"


def test_filter_by_completed_false():
    """filter_tasks(completed=False) should exclude finished tasks."""
    owner = Owner("Jordan")
    scheduler = Scheduler(owner)
    done = make_task("Done"); done.mark_complete()
    pending = make_task("Pending")
    result = scheduler.filter_tasks([done, pending], completed=False)
    assert len(result) == 1
    assert result[0].title == "Pending"


def test_filter_combined():
    """Combining pet_name and priority filters should apply both."""
    owner = Owner("Jordan")
    scheduler = Scheduler(owner)
    t1 = make_task("A", priority=Priority.HIGH); t1.pet_name = "Mochi"
    t2 = make_task("B", priority=Priority.LOW);  t2.pet_name = "Mochi"
    t3 = make_task("C", priority=Priority.HIGH); t3.pet_name = "Luna"
    result = scheduler.filter_tasks([t1, t2, t3], pet_name="Mochi", priority=Priority.HIGH)
    assert len(result) == 1
    assert result[0].title == "A"


# ---------------------------------------------------------------------------
# Recurring task auto-spawn tests
# ---------------------------------------------------------------------------

def test_complete_recurring_task_spawns_next():
    """Completing a recurring task via Pet.complete_task() should add a new task."""
    pet = make_pet()
    task = Task("Breakfast", TaskType.FEEDING, 10, Priority.HIGH,
                is_recurring=True, recurrence_interval_hours=12)
    pet.add_task(task)
    assert len(pet.tasks) == 1
    pet.complete_task(task.id)
    assert len(pet.tasks) == 2
    assert pet.tasks[0].completed is True
    assert pet.tasks[1].completed is False
    assert pet.tasks[1].title == "Breakfast"


def test_complete_nonrecurring_task_does_not_spawn():
    """Completing a non-recurring task should not add a new task."""
    pet = make_pet()
    task = make_task("One-off walk")
    pet.add_task(task)
    pet.complete_task(task.id)
    assert len(pet.tasks) == 1
    assert pet.tasks[0].completed is True


def test_recurring_next_scheduled_time_is_offset():
    """The spawned task's scheduled_time should be interval hours after the original."""
    from datetime import timedelta
    pet = make_pet()
    base_time = datetime(2026, 1, 1, 8, 0)
    task = Task("Meds", TaskType.MEDICATION, 5, Priority.HIGH,
                scheduled_time=base_time, is_recurring=True,
                recurrence_interval_hours=24)
    pet.add_task(task)
    pet.complete_task(task.id)
    spawned = pet.tasks[1]
    assert spawned.scheduled_time == base_time + timedelta(hours=24)


# ---------------------------------------------------------------------------
# Conflict detection tests
# ---------------------------------------------------------------------------

def test_detect_conflicts_finds_overlap():
    """Two entries whose windows overlap should be returned as a conflict pair."""
    owner = Owner("Jordan", available_start="08:00", available_end="20:00")
    scheduler = Scheduler(owner)
    today = datetime.today().replace(second=0, microsecond=0)
    t1 = make_task("Vet",      duration=60, scheduled_time=today.replace(hour=10))
    t2 = make_task("Grooming", duration=45, scheduled_time=today.replace(hour=10, minute=30))
    pet = make_pet()
    pet.add_task(t1); pet.add_task(t2)
    owner.add_pet(pet)
    schedule = scheduler.generate_schedule()
    conflicts = scheduler.detect_conflicts(schedule)
    assert len(conflicts) >= 1


def test_detect_conflicts_no_overlap():
    """Non-overlapping entries should produce no conflicts."""
    owner = Owner("Jordan", available_start="08:00", available_end="20:00")
    scheduler = Scheduler(owner)
    today = datetime.today().replace(second=0, microsecond=0)
    t1 = make_task("Walk",  duration=30, scheduled_time=today.replace(hour=8))
    t2 = make_task("Feed",  duration=10, scheduled_time=today.replace(hour=9))
    pet = make_pet()
    pet.add_task(t1); pet.add_task(t2)
    owner.add_pet(pet)
    schedule = scheduler.generate_schedule()
    conflicts = scheduler.detect_conflicts(schedule)
    assert conflicts == []
