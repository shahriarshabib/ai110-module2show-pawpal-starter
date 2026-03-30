# PawPal+ Project Reflection

## 1. System Design

### Three Core User Actions

1. **Add a pet** — An owner registers a pet (name, species, age) so the system can track tasks specific to that animal.
2. **Schedule a care task** — An owner assigns a task (e.g., morning walk, medication) to a pet with a priority, duration, and optional time, so it can be planned automatically.
3. **View today's schedule** — The owner asks the system to generate an ordered daily plan that fits within their available hours, with a plain-English explanation of why each task was placed when it was.

---

**a. Initial design**

The system is organised around four classes:

| Class | Responsibility |
|---|---|
| `Task` (dataclass) | Stores everything about one care action: title, type, duration, priority, scheduled time, and recurrence. Knows whether it is overdue and when it next repeats. |
| `Pet` (dataclass) | Represents a single animal. Holds a list of `Task` objects and provides helpers to filter by priority or type. |
| `Owner` | Represents the person managing care. Owns a list of `Pet` objects and knows their daily availability window (start/end times). |
| `Scheduler` | Contains the algorithmic logic: sort tasks by priority, detect time conflicts, and produce a complete day plan with explanations. |

Relationships: `Owner` *has many* `Pet` objects; each `Pet` *has many* `Task` objects; `Scheduler` *uses* an `Owner` (and transitively all its pets and tasks) to build the plan.

Two supporting enums keep priority levels (`Priority`) and task categories (`TaskType`) explicit and type-safe rather than raw strings.

**b. Design changes**

After reviewing the skeleton for missing relationships and logic bottlenecks, three problems were identified and fixed:

1. **Added `id` and `pet_name` fields to `Task`.**
   The original `remove_task` matched by title, which would silently fail (or remove the wrong task) if two tasks shared the same name. Replacing title-matching with a `uuid`-based `id` makes removal reliable. A `pet_name` field was also added so tasks carry their owner-pet label with them; without it, the `Scheduler` would have no way to produce entries like "Feed Mochi" after flattening all tasks into a single list. This field is stamped by `Pet.add_task()`.

2. **Introduced a `ScheduleEntry` dataclass.**
   `Scheduler._schedule` was originally `list[dict]`, which is untyped and fragile — any code consuming the schedule would need to know the exact key names by convention. Replacing it with a proper `ScheduleEntry(pet_name, task, start_time, end_time, reason)` dataclass makes the contract explicit, catches attribute errors early, and makes it straightforward to display the schedule in a Streamlit table via `dataclasses.asdict()`.

3. **Updated `detect_conflicts` to operate on `list[ScheduleEntry]` instead of `list[Task]`.**
   Conflict detection needs concrete `start_time`/`end_time` values, which only exist after scheduling. Tasks before scheduling may have no `scheduled_time`, so checking them directly would always be incomplete. Working on `ScheduleEntry` objects (post-placement) is the correct stage.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
