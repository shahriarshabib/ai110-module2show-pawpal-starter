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

The scheduler considers three constraints, applied in this order:

1. **Owner availability window** (hard constraint) — any task that would end after `available_end` is silently skipped; the window is absolute.
2. **Fixed scheduled_time** (hard constraint) — tasks with a user-specified time are placed at exactly that time, regardless of priority.
3. **Priority** (soft constraint) — among flexible tasks, HIGH > MEDIUM > LOW determines slot order.

Priority was chosen as the tiebreaker over duration because a 5-minute medication at HIGH priority is more important to the pet's health than a 30-minute LOW-priority play session, even if the play session would "fit better" in the gap.

**b. Tradeoffs**

The scheduler checks for conflicts *after* placing tasks rather than preventing them upfront. Specifically, `detect_conflicts()` flags overlapping `ScheduleEntry` windows as a warning message instead of refusing to place a task.

**Why this is reasonable:** A strict "refuse on conflict" approach would silently drop fixed-time tasks that overlap — which could mean a medication is skipped without the owner knowing. Showing a warning instead keeps all tasks visible and lets the human decide what to reschedule. The tradeoff is that the generated schedule can technically be invalid, but it favours transparency over false correctness.

---

## 3. AI Collaboration

**a. How you used AI**

AI was used at every phase of this project, but the role shifted as the work progressed:

- **Design brainstorming (Phase 1):** AI generated the initial Mermaid.js UML diagram from a plain-English description of the four classes. This was the fastest part — describing the system in natural language and getting a structured diagram in seconds was far quicker than drawing it by hand. The most useful prompt pattern was: *"Here are my four classes and their attributes — generate a class diagram showing relationships."*

- **Code scaffolding (Phase 2):** AI filled in method stubs from the UML. The most helpful prompts were specific: *"Implement `generate_schedule()` so that fixed-time tasks are placed first, then flexible tasks fill remaining gaps in priority order."* Vague prompts like *"implement the scheduler"* produced overly complex results.

- **Algorithm review (Phases 3–4):** AI was used as a "reviewer" by sharing a method and asking *"What edge cases is this missing?"* This surfaced the `detect_conflicts` timing issue (operating on Tasks before scheduling vs. on ScheduleEntry after) and the recurring task spawn problem.

- **Test generation (Phase 5):** AI generated test stubs well, but tended to write only happy-path tests. Prompting specifically for *"edge cases and failure modes"* was necessary to get tests like `test_filter_empty_input_returns_empty_list` and `test_complete_task_bad_id_returns_false`.

**b. Judgment and verification**

One AI suggestion that was modified: when asked to implement `detect_conflicts()`, the AI's first version compared `Task` objects directly using their `scheduled_time` attribute. This would have worked for tasks with a fixed time, but silently produced no conflicts for flexible tasks (which have `scheduled_time = None`). The issue was that conflicts only exist *after* the scheduler assigns times — not before.

The fix was to move conflict detection downstream to operate on `ScheduleEntry` objects instead of `Task` objects. The AI's approach was verified by writing a test with two overlapping flexible tasks and confirming that the original version returned no conflicts where it should have found one.

The rule applied: *if a method's inputs don't contain all the information needed to compute its output, the method is operating at the wrong stage.*

---

## 4. Testing and Verification

**a. What you tested**

The test suite covers 40 behaviours across five categories:

1. **Task lifecycle** — `mark_complete()` flips status; `is_overdue()` respects completion state and reference time; `to_dict()` produces the expected keys.
2. **Pet management** — `add_task()` stamps `pet_name`; `remove_task()` uses id not title; duplicate prevention; `complete_task()` auto-spawns recurring tasks.
3. **Owner management** — Pet aggregation, duplicate guard, `available_minutes()` arithmetic.
4. **Scheduling algorithms** — Priority ordering, time window enforcement (skip if too long, include if exactly fits), sort by time (ascending, unscheduled last), multi-criteria filter.
5. **Conflict detection** — Overlapping windows detected; non-overlapping windows clean; exact same start time flagged.

Edge cases were the most valuable tests. `test_schedule_empty_when_pet_has_no_tasks`, `test_filter_empty_input_returns_empty_list`, and `test_explain_plan_before_generate_returns_safe_message` all test defensive behaviour that would otherwise only surface as confusing runtime errors in the UI.

**b. Confidence**

★★★★☆ (4/5)

The core scheduling logic is thoroughly tested and handles the known edge cases. Confidence is not 5/5 because:
- The Streamlit session-state interactions (e.g., what happens if a user completes a task mid-schedule) are not covered by automated tests.
- The scheduler assumes all tasks happen on a single day; multi-day scheduling is untested territory.
- If given more time, the next edge cases to test would be: tasks whose recurrence spans midnight, an owner with 10+ pets and 50+ tasks (performance), and concurrent session-state mutations.

---

## 5. Reflection

**a. What went well**

The clean separation between the logic layer (`pawpal_system.py`) and the UI layer (`app.py`) worked very well in practice. Because all intelligence lives in `Scheduler`, `Pet`, and `Task`, the Streamlit UI became thin wiring code. When a new feature was added to the backend (e.g., `filter_tasks()`), it appeared in the UI with just a few lines in `app.py`. This "CLI-first" workflow also made testing straightforward — all 40 tests run against pure Python with no Streamlit dependency.

**b. What you would improve**

The scheduler is "greedy" — it places tasks in priority order without looking ahead. A greedy scheduler can leave a large gap in the morning because it placed a 5-minute HIGH-priority task there, then skips a 60-minute MEDIUM-priority appointment that would have fit. A better approach would be a bin-packing or interval-scheduling algorithm that maximises total scheduled time. This would be the first algorithmic redesign in a second iteration.

**c. Key takeaway**

The most important lesson was: **AI is a fast first-drafter, not a final architect.** AI could generate a working skeleton in minutes, but it consistently produced designs that were one level too shallow — missing `ScheduleEntry`, missing the `pet_name` stamp, operating conflict detection at the wrong stage. The value of the human role was not writing code faster than AI, but knowing *what questions to ask* to expose the gaps. The prompts that produced the best results were always the ones that started with a constraint or a failure scenario, not a feature request.
