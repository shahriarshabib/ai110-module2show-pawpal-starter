# PawPal+ — Final UML Class Diagram

Paste the Mermaid code below into https://mermaid.live to render the diagram.

```mermaid
classDiagram
    class Priority {
        <<enumeration>>
        LOW
        MEDIUM
        HIGH
        +numeric() int
    }

    class TaskType {
        <<enumeration>>
        FEEDING
        WALK
        MEDICATION
        APPOINTMENT
        GROOMING
        PLAY
        OTHER
    }

    class Task {
        +str id
        +str title
        +TaskType task_type
        +int duration_minutes
        +Priority priority
        +datetime scheduled_time
        +bool is_recurring
        +int recurrence_interval_hours
        +str notes
        +str pet_name
        +bool completed
        +mark_complete() Task
        +is_overdue(reference_time) bool
        +next_occurrence() datetime
        +to_dict() dict
    }

    class Pet {
        +str name
        +str species
        +float age
        +str breed
        +List~Task~ tasks
        +add_task(task)
        +remove_task(task_id) bool
        +complete_task(task_id) bool
        +get_tasks_by_priority(priority) List~Task~
        +get_tasks_by_type(task_type) List~Task~
    }

    class Owner {
        +str name
        +str available_start
        +str available_end
        +List~Pet~ pets
        +add_pet(pet)
        +remove_pet(name) bool
        +get_all_tasks() List~Task~
        +available_minutes() int
    }

    class ScheduleEntry {
        +str pet_name
        +Task task
        +datetime start_time
        +datetime end_time
        +str reason
        +to_dict() dict
    }

    class Scheduler {
        +Owner owner
        -List~ScheduleEntry~ _schedule
        +sort_by_priority(tasks) List~Task~
        +sort_by_time(tasks) List~Task~
        +filter_tasks(tasks, pet_name, completed, task_type, priority) List~Task~
        +detect_conflicts(entries) List~tuple~
        +generate_schedule(date) List~ScheduleEntry~
        +explain_plan() str
        +get_schedule() List~ScheduleEntry~
    }

    Owner "1" --> "0..*" Pet : owns
    Pet "1" --> "0..*" Task : has
    Scheduler --> Owner : uses
    Scheduler --> ScheduleEntry : produces
    ScheduleEntry --> Task : references
    Task --> Priority : uses
    Task --> TaskType : uses
    Task ..> Task : mark_complete returns next occurrence
```

## Changes from Phase 1 skeleton

| Change | Reason |
|---|---|
| Added `id: str` to `Task` | Reliable removal by UUID instead of fragile title-matching |
| Added `pet_name: str` to `Task` | Stamped by `Pet.add_task()` so Scheduler can label entries without back-reference |
| Added `completed: bool` to `Task` | Needed for filter logic and overdue detection |
| `mark_complete()` now returns `Task` (nullable) | Enables recurring auto-spawn pattern |
| Added `Pet.complete_task(id)` | Encapsulates "mark done + spawn next" in one atomic operation |
| Added `ScheduleEntry` dataclass | Replaces untyped `dict`; typed contract for schedule consumers |
| Added `Scheduler.sort_by_time()` | Separate sort key from priority sort |
| Added `Scheduler.filter_tasks()` | Multi-criteria AND filter used in Tasks tab |
| `detect_conflicts()` operates on `ScheduleEntry` not `Task` | Conflicts only make sense post-placement when times are concrete |
| Added `ScheduleEntry.to_dict()` | Streamlit-friendly serialisation |
