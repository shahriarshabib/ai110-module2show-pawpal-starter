"""
PawPal+ — Backend logic layer.

Classes
-------
Task      : A single care action for a pet (dataclass).
Pet       : A pet with its own task list (dataclass).
Owner     : A person who owns one or more pets.
Scheduler : Builds and explains a daily care schedule.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

    def numeric(self) -> int:
        """Return a numeric weight for sorting (higher = more urgent)."""
        return {"low": 1, "medium": 2, "high": 3}[self.value]


class TaskType(str, Enum):
    FEEDING = "feeding"
    WALK = "walk"
    MEDICATION = "medication"
    APPOINTMENT = "appointment"
    GROOMING = "grooming"
    PLAY = "play"
    OTHER = "other"


# ---------------------------------------------------------------------------
# Task
# ---------------------------------------------------------------------------

@dataclass
class Task:
    """Represents a single care action to perform for a pet."""

    title: str
    task_type: TaskType
    duration_minutes: int
    priority: Priority = Priority.MEDIUM
    scheduled_time: Optional[datetime] = None   # wall-clock start time if known
    is_recurring: bool = False
    recurrence_interval_hours: Optional[int] = None  # e.g. 8 for every 8 hours
    notes: str = ""
    pet_name: str = ""          # stamped by Pet.add_task() — lets Scheduler label entries
    id: str = field(default_factory=lambda: str(uuid.uuid4()))  # unique ID for reliable removal

    # ------------------------------------------------------------------
    # Methods (stubs — implement in later phases)
    # ------------------------------------------------------------------

    def is_overdue(self, reference_time: Optional[datetime] = None) -> bool:
        """Return True if the task's scheduled_time has passed."""
        # TODO: compare scheduled_time to reference_time (or datetime.now())
        pass

    def next_occurrence(self) -> Optional[datetime]:
        """Return the next scheduled_time for a recurring task."""
        # TODO: add recurrence_interval_hours to scheduled_time
        pass

    def to_dict(self) -> dict:
        """Serialize to a plain dict (useful for Streamlit tables)."""
        # TODO: return all fields as a JSON-serialisable dict
        pass


# ---------------------------------------------------------------------------
# Pet
# ---------------------------------------------------------------------------

@dataclass
class Pet:
    """Represents a pet and the tasks associated with its care."""

    name: str
    species: str          # e.g. "dog", "cat", "rabbit"
    age: float            # years
    breed: str = ""
    tasks: list[Task] = field(default_factory=list)

    # ------------------------------------------------------------------
    # Methods (stubs)
    # ------------------------------------------------------------------

    def add_task(self, task: Task) -> None:
        """Stamp pet_name onto the task, then append it to this pet's task list."""
        # TODO: validate task type is appropriate for species, then stamp and append
        pass

    def remove_task(self, task_id: str) -> bool:
        """Remove the task with the given id; return True if found."""
        # TODO: search tasks by task.id (not title), pop if found
        pass

    def get_tasks_by_priority(self, priority: Priority) -> list[Task]:
        """Return all tasks with the given priority level."""
        # TODO: filter self.tasks by priority
        pass

    def get_tasks_by_type(self, task_type: TaskType) -> list[Task]:
        """Return all tasks of the given type."""
        # TODO: filter self.tasks by task_type
        pass


# ---------------------------------------------------------------------------
# Owner
# ---------------------------------------------------------------------------

class Owner:
    """Represents a pet owner who manages one or more pets."""

    def __init__(self, name: str, available_start: str = "08:00",
                 available_end: str = "20:00") -> None:
        self.name = name
        self.available_start = available_start  # "HH:MM" 24-hour format
        self.available_end = available_end
        self.pets: list[Pet] = []

    # ------------------------------------------------------------------
    # Methods (stubs)
    # ------------------------------------------------------------------

    def add_pet(self, pet: Pet) -> None:
        """Register a pet under this owner."""
        # TODO: append pet to self.pets (guard against duplicates by name)
        pass

    def remove_pet(self, name: str) -> bool:
        """Remove a pet by name; return True if found."""
        # TODO: find pet by name and remove from list
        pass

    def get_all_tasks(self) -> list[Task]:
        """Return every task across all pets (flat list)."""
        # TODO: flatten [pet.tasks for pet in self.pets]
        pass

    def available_minutes(self) -> int:
        """Return total available minutes in the owner's window."""
        # TODO: parse available_start / available_end and compute difference
        pass


# ---------------------------------------------------------------------------
# ScheduleEntry  (replaces the untyped dict that Scheduler used to return)
# ---------------------------------------------------------------------------

@dataclass
class ScheduleEntry:
    """One slot in a generated daily schedule."""

    pet_name: str
    task: Task
    start_time: datetime
    end_time: datetime
    reason: str = ""   # plain-English explanation of why/when this was placed


# ---------------------------------------------------------------------------
# Scheduler
# ---------------------------------------------------------------------------

class Scheduler:
    """Builds a prioritised daily care schedule for an owner's pets."""

    def __init__(self, owner: Owner) -> None:
        self.owner = owner
        self._schedule: list[ScheduleEntry] = []  # populated by generate_schedule()

    # ------------------------------------------------------------------
    # Core scheduling methods (stubs)
    # ------------------------------------------------------------------

    def sort_by_priority(self, tasks: list[Task]) -> list[Task]:
        """Return tasks sorted descending by priority, then by scheduled_time."""
        # TODO: use Priority.numeric() as the sort key
        pass

    def detect_conflicts(self, entries: list[ScheduleEntry]) -> list[tuple[ScheduleEntry, ScheduleEntry]]:
        """Return pairs of entries whose time windows overlap."""
        # TODO: for each consecutive pair check if start_time + duration overlaps next start_time
        pass

    def generate_schedule(self, date: Optional[datetime] = None) -> list[ScheduleEntry]:
        """
        Build a day plan for the given date.

        Returns a list of ScheduleEntry objects (typed, Streamlit-friendly).
        """
        # TODO:
        #   1. Collect all tasks from owner.get_all_tasks()
        #   2. Sort by priority (and fixed scheduled_time if set)
        #   3. Fit tasks into the owner's available window
        #   4. Flag conflicts; skip or reschedule low-priority tasks
        #   5. Build ScheduleEntry objects, populate self._schedule, and return it
        pass

    def explain_plan(self) -> str:
        """Return a human-readable explanation of the current schedule."""
        # TODO: iterate self._schedule and build a formatted string
        pass

    def get_schedule(self) -> list[ScheduleEntry]:
        """Return the most recently generated schedule."""
        return self._schedule
