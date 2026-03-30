"""
PawPal+ — Backend logic layer.

Classes
-------
Task          : A single care action for a pet (dataclass).
Pet           : A pet with its own task list (dataclass).
Owner         : A person who owns one or more pets.
ScheduleEntry : One typed slot in a generated daily schedule.
Scheduler     : Builds and explains a daily care schedule.
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
    scheduled_time: Optional[datetime] = None
    is_recurring: bool = False
    recurrence_interval_hours: Optional[int] = None
    notes: str = ""
    pet_name: str = ""
    completed: bool = False
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def mark_complete(self) -> None:
        """Mark this task as completed."""
        self.completed = True

    def is_overdue(self, reference_time: Optional[datetime] = None) -> bool:
        """Return True if the task's scheduled_time has passed and it is not completed."""
        if self.scheduled_time is None:
            return False
        ref = reference_time or datetime.now()
        return not self.completed and self.scheduled_time < ref

    def next_occurrence(self) -> Optional[datetime]:
        """Return the next scheduled_time for a recurring task, or None if not recurring."""
        if not self.is_recurring or self.recurrence_interval_hours is None:
            return None
        base = self.scheduled_time or datetime.now()
        return base + timedelta(hours=self.recurrence_interval_hours)

    def to_dict(self) -> dict:
        """Serialize to a plain dict suitable for Streamlit tables."""
        return {
            "id": self.id,
            "title": self.title,
            "type": self.task_type.value,
            "duration_min": self.duration_minutes,
            "priority": self.priority.value,
            "scheduled_time": self.scheduled_time.strftime("%H:%M") if self.scheduled_time else "",
            "recurring": self.is_recurring,
            "completed": self.completed,
            "pet": self.pet_name,
            "notes": self.notes,
        }


# ---------------------------------------------------------------------------
# Pet
# ---------------------------------------------------------------------------

@dataclass
class Pet:
    """Represents a pet and the tasks associated with its care."""

    name: str
    species: str
    age: float
    breed: str = ""
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Stamp pet_name onto the task and append it to this pet's task list."""
        task.pet_name = self.name
        self.tasks.append(task)

    def remove_task(self, task_id: str) -> bool:
        """Remove the task with the given id; return True if found."""
        for i, t in enumerate(self.tasks):
            if t.id == task_id:
                self.tasks.pop(i)
                return True
        return False

    def get_tasks_by_priority(self, priority: Priority) -> list[Task]:
        """Return all tasks with the given priority level."""
        return [t for t in self.tasks if t.priority == priority]

    def get_tasks_by_type(self, task_type: TaskType) -> list[Task]:
        """Return all tasks of the given type."""
        return [t for t in self.tasks if t.task_type == task_type]


# ---------------------------------------------------------------------------
# Owner
# ---------------------------------------------------------------------------

class Owner:
    """Represents a pet owner who manages one or more pets."""

    def __init__(self, name: str, available_start: str = "08:00",
                 available_end: str = "20:00") -> None:
        self.name = name
        self.available_start = available_start
        self.available_end = available_end
        self.pets: list[Pet] = []

    def add_pet(self, pet: Pet) -> None:
        """Register a pet; silently ignores duplicates by name."""
        if not any(p.name == pet.name for p in self.pets):
            self.pets.append(pet)

    def remove_pet(self, name: str) -> bool:
        """Remove a pet by name; return True if found."""
        for i, p in enumerate(self.pets):
            if p.name == name:
                self.pets.pop(i)
                return True
        return False

    def get_all_tasks(self) -> list[Task]:
        """Return every task across all pets as a flat list."""
        return [task for pet in self.pets for task in pet.tasks]

    def available_minutes(self) -> int:
        """Return total available care minutes in the owner's daily window."""
        fmt = "%H:%M"
        start = datetime.strptime(self.available_start, fmt)
        end = datetime.strptime(self.available_end, fmt)
        return int((end - start).total_seconds() // 60)


# ---------------------------------------------------------------------------
# ScheduleEntry
# ---------------------------------------------------------------------------

@dataclass
class ScheduleEntry:
    """One typed slot in a generated daily schedule."""

    pet_name: str
    task: Task
    start_time: datetime
    end_time: datetime
    reason: str = ""

    def to_dict(self) -> dict:
        """Serialize to a plain dict suitable for Streamlit tables."""
        return {
            "pet": self.pet_name,
            "task": self.task.title,
            "type": self.task.task_type.value,
            "priority": self.task.priority.value,
            "start": self.start_time.strftime("%H:%M"),
            "end": self.end_time.strftime("%H:%M"),
            "duration_min": self.task.duration_minutes,
            "reason": self.reason,
        }


# ---------------------------------------------------------------------------
# Scheduler
# ---------------------------------------------------------------------------

class Scheduler:
    """Builds a prioritised daily care schedule for an owner's pets."""

    def __init__(self, owner: Owner) -> None:
        self.owner = owner
        self._schedule: list[ScheduleEntry] = []

    def sort_by_priority(self, tasks: list[Task]) -> list[Task]:
        """Return tasks sorted descending by priority; fixed-time tasks come first within each tier."""
        def sort_key(t: Task):
            time_key = t.scheduled_time or datetime.max
            return (-t.priority.numeric(), time_key)
        return sorted(tasks, key=sort_key)

    def detect_conflicts(self, entries: list[ScheduleEntry]) -> list[tuple[ScheduleEntry, ScheduleEntry]]:
        """Return pairs of entries whose time windows overlap."""
        conflicts = []
        sorted_entries = sorted(entries, key=lambda e: e.start_time)
        for i in range(len(sorted_entries) - 1):
            a = sorted_entries[i]
            b = sorted_entries[i + 1]
            if a.end_time > b.start_time:
                conflicts.append((a, b))
        return conflicts

    def generate_schedule(self, date: Optional[datetime] = None) -> list[ScheduleEntry]:
        """
        Build a day plan for the given date.

        Fixed-time tasks are placed at their scheduled_time; remaining tasks
        are slotted sequentially after the last placed task, in priority order.
        Tasks that exceed the owner's available window are skipped.
        """
        today = (date or datetime.now()).replace(hour=0, minute=0, second=0, microsecond=0)
        fmt = "%H:%M"
        window_start = datetime.strptime(self.owner.available_start, fmt).replace(
            year=today.year, month=today.month, day=today.day)
        window_end = datetime.strptime(self.owner.available_end, fmt).replace(
            year=today.year, month=today.month, day=today.day)

        all_tasks = self.sort_by_priority(self.owner.get_all_tasks())

        fixed: list[Task] = []
        flexible: list[Task] = []
        for t in all_tasks:
            if t.scheduled_time is not None:
                fixed.append(t)
            else:
                flexible.append(t)

        entries: list[ScheduleEntry] = []

        # Place fixed-time tasks first
        for task in fixed:
            start = task.scheduled_time.replace(
                year=today.year, month=today.month, day=today.day)
            end = start + timedelta(minutes=task.duration_minutes)
            if start >= window_start and end <= window_end:
                entries.append(ScheduleEntry(
                    pet_name=task.pet_name,
                    task=task,
                    start_time=start,
                    end_time=end,
                    reason=f"Fixed appointment at {start.strftime('%H:%M')} "
                           f"({task.priority.value} priority)",
                ))

        # Slot flexible tasks into remaining time
        cursor = window_start
        for task in flexible:
            # Advance cursor past any fixed entry that occupies this slot
            for entry in sorted(entries, key=lambda e: e.start_time):
                if entry.start_time < cursor + timedelta(minutes=task.duration_minutes) \
                        and entry.end_time > cursor:
                    cursor = entry.end_time

            end = cursor + timedelta(minutes=task.duration_minutes)
            if end > window_end:
                continue  # doesn't fit — skip

            entries.append(ScheduleEntry(
                pet_name=task.pet_name,
                task=task,
                start_time=cursor,
                end_time=end,
                reason=f"Scheduled at {cursor.strftime('%H:%M')} "
                       f"({task.priority.value} priority)",
            ))
            cursor = end

        self._schedule = sorted(entries, key=lambda e: e.start_time)
        return self._schedule

    def explain_plan(self) -> str:
        """Return a human-readable explanation of the current schedule."""
        if not self._schedule:
            return "No schedule generated yet. Call generate_schedule() first."
        lines = [f"=== Daily Schedule for {self.owner.name} ===\n"]
        for entry in self._schedule:
            lines.append(
                f"  {entry.start_time.strftime('%H:%M')} - {entry.end_time.strftime('%H:%M')} "
                f"| [{entry.task.priority.value.upper()}] {entry.task.title} "
                f"({entry.pet_name}, {entry.task.duration_minutes} min)"
            )
            if entry.reason:
                lines.append(f"    -> {entry.reason}")
        conflicts = self.detect_conflicts(self._schedule)
        if conflicts:
            lines.append("\n[!] Conflicts detected:")
            for a, b in conflicts:
                lines.append(f"  '{a.task.title}' overlaps with '{b.task.title}'")
        return "\n".join(lines)

    def get_schedule(self) -> list[ScheduleEntry]:
        """Return the most recently generated schedule."""
        return self._schedule
