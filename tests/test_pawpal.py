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
