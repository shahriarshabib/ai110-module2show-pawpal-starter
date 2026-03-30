"""
app.py — PawPal+ Streamlit UI.

Wires the Owner / Pet / Task / Scheduler backend into an interactive app.
Session state acts as the app's persistent memory so objects survive reruns.
"""

import streamlit as st
from datetime import datetime
from pawpal_system import Owner, Pet, Task, TaskType, Priority, Scheduler

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="wide")
st.title("🐾 PawPal+")
st.caption("Smart pet care scheduling — powered by Python OOP")

# ---------------------------------------------------------------------------
# Session-state initialisation
# ---------------------------------------------------------------------------
if "owner" not in st.session_state:
    st.session_state.owner = None

# ---------------------------------------------------------------------------
# Owner setup screen (shown only until an owner is created)
# ---------------------------------------------------------------------------
if st.session_state.owner is None:
    st.subheader("Welcome! Set up your profile to get started.")
    with st.form("owner_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            owner_name  = st.text_input("Your name", value="Jordan")
        with col2:
            avail_start = st.text_input("Available from (HH:MM)", value="08:00")
        with col3:
            avail_end   = st.text_input("Available until (HH:MM)", value="20:00")
        submitted = st.form_submit_button("Create profile", use_container_width=True)

    if submitted and owner_name.strip():
        st.session_state.owner = Owner(
            name=owner_name.strip(),
            available_start=avail_start,
            available_end=avail_end,
        )
        st.rerun()
    st.stop()

owner: Owner = st.session_state.owner

# ---------------------------------------------------------------------------
# Sidebar — owner summary + reset
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header(f"👤 {owner.name}")
    st.caption(f"Available {owner.available_start} – {owner.available_end}")
    st.metric("Available minutes", owner.available_minutes())
    st.metric("Pets registered", len(owner.pets))
    total   = len(owner.get_all_tasks())
    done    = sum(1 for t in owner.get_all_tasks() if t.completed)
    pending = total - done
    st.metric("Tasks (total)", total)
    if total:
        cols = st.columns(2)
        cols[0].metric("Pending", pending)
        cols[1].metric("Done", done)

    st.divider()
    overdue = [t for t in owner.get_all_tasks() if t.is_overdue()]
    if overdue:
        st.warning(f"⚠ {len(overdue)} overdue task(s)")
        for t in overdue:
            st.caption(f"  • {t.pet_name}: {t.title}")

    st.divider()
    if st.button("Reset / Switch owner", use_container_width=True):
        st.session_state.owner = None
        st.rerun()

# ---------------------------------------------------------------------------
# Tab layout
# ---------------------------------------------------------------------------
tab_pets, tab_tasks, tab_schedule = st.tabs(["🐶 Pets", "📋 Tasks", "📅 Schedule"])

# ============================================================
# TAB 1 — Pets
# ============================================================
with tab_pets:
    st.subheader("Your Pets")

    with st.expander("➕ Add a new pet", expanded=len(owner.pets) == 0):
        with st.form("add_pet_form"):
            col1, col2 = st.columns(2)
            with col1:
                pet_name = st.text_input("Pet name")
                species  = st.selectbox("Species", ["dog", "cat", "rabbit", "bird", "other"])
            with col2:
                age   = st.number_input("Age (years)", min_value=0.0, max_value=30.0,
                                        step=0.5, value=1.0)
                breed = st.text_input("Breed (optional)")
            add_pet = st.form_submit_button("Add pet", use_container_width=True)

        if add_pet:
            if not pet_name.strip():
                st.warning("Please enter a pet name.")
            elif any(p.name == pet_name.strip() for p in owner.pets):
                st.warning(f"'{pet_name}' is already registered.")
            else:
                owner.add_pet(Pet(name=pet_name.strip(), species=species,
                                  age=age, breed=breed))
                st.success(f"✅ {pet_name} added!")
                st.rerun()

    if not owner.pets:
        st.info("No pets yet — add one above to get started.")
    else:
        for pet in owner.pets:
            pending_count = sum(1 for t in pet.tasks if not t.completed)
            label = (f"**{pet.name}** — {pet.species}"
                     f"{', ' + pet.breed if pet.breed else ''}"
                     f", {pet.age}y  |  {pending_count} pending task(s)")
            with st.expander(label):
                if pet.tasks:
                    rows = []
                    for t in pet.tasks:
                        d = t.to_dict()
                        d.pop("id", None)          # hide uuid from display
                        d.pop("pet", None)          # redundant inside pet expander
                        rows.append(d)
                    st.dataframe(rows, use_container_width=True)
                else:
                    st.caption("No tasks yet.")
                if st.button(f"Remove {pet.name}", key=f"del_{pet.name}",
                             type="secondary"):
                    owner.remove_pet(pet.name)
                    st.rerun()

# ============================================================
# TAB 2 — Tasks
# ============================================================
with tab_tasks:
    left, right = st.columns([1, 1], gap="large")

    # --- Add task form (left column) ---
    with left:
        st.subheader("Add a Task")
        if not owner.pets:
            st.info("Add a pet first.")
        else:
            with st.form("add_task_form"):
                pet_choice   = st.selectbox("Assign to pet", [p.name for p in owner.pets])
                task_title   = st.text_input("Task title", value="Morning walk")
                col1, col2   = st.columns(2)
                with col1:
                    task_type    = st.selectbox("Type", [t.value for t in TaskType])
                    priority_val = st.selectbox("Priority",
                                                [p.value for p in Priority], index=1)
                with col2:
                    duration     = st.number_input("Duration (min)", min_value=1,
                                                   max_value=480, value=20)
                    has_time     = st.checkbox("Fixed time?")
                    sched_hour   = st.number_input("Hour", min_value=0, max_value=23,
                                                   value=8, disabled=not has_time)
                    sched_min    = st.number_input("Minute", min_value=0, max_value=59,
                                                   value=0, disabled=not has_time)
                is_recurring = st.checkbox("Recurring?")
                recur_hours  = st.number_input("Repeat every N hours", min_value=1,
                                               max_value=168, value=24,
                                               disabled=not is_recurring)
                notes     = st.text_input("Notes (optional)")
                add_task  = st.form_submit_button("Add task", use_container_width=True)

            if add_task:
                scheduled_time = None
                if has_time:
                    scheduled_time = datetime.today().replace(
                        hour=int(sched_hour), minute=int(sched_min),
                        second=0, microsecond=0)
                new_task = Task(
                    title=task_title.strip() or "Unnamed task",
                    task_type=TaskType(task_type),
                    duration_minutes=int(duration),
                    priority=Priority(priority_val),
                    scheduled_time=scheduled_time,
                    is_recurring=is_recurring,
                    recurrence_interval_hours=int(recur_hours) if is_recurring else None,
                    notes=notes,
                )
                target_pet = next(p for p in owner.pets if p.name == pet_choice)
                target_pet.add_task(new_task)
                st.success(f"✅ '{new_task.title}' added to {pet_choice}.")
                st.rerun()

    # --- Filtered task view (right column) ---
    with right:
        st.subheader("Browse & Complete Tasks")
        all_tasks = owner.get_all_tasks()
        if not all_tasks:
            st.info("No tasks yet.")
        else:
            scheduler = Scheduler(owner)

            # Filter controls
            fc1, fc2, fc3 = st.columns(3)
            pet_filter    = fc1.selectbox("Pet", ["All"] + [p.name for p in owner.pets],
                                          key="f_pet")
            status_filter = fc2.selectbox("Status", ["All", "Pending", "Completed"],
                                          key="f_status")
            sort_by       = fc3.selectbox("Sort by", ["Priority", "Time"],
                                          key="f_sort")

            filtered = scheduler.filter_tasks(
                all_tasks,
                pet_name  = None if pet_filter == "All" else pet_filter,
                completed = None if status_filter == "All"
                            else (status_filter == "Completed"),
            )
            sorted_tasks = (scheduler.sort_by_time(filtered) if sort_by == "Time"
                            else scheduler.sort_by_priority(filtered))

            if not sorted_tasks:
                st.info("No tasks match the current filters.")
            else:
                st.caption(f"{len(sorted_tasks)} task(s) shown")
                for t in sorted_tasks:
                    badge = "✅" if t.completed else ("🔴" if t.is_overdue() else "⏳")
                    time_str = (t.scheduled_time.strftime("%H:%M")
                                if t.scheduled_time else "flexible")
                    label = (f"{badge} **{t.title}** — {t.pet_name} | "
                             f"{t.priority.value} | {time_str} | {t.duration_minutes} min"
                             + (" 🔁" if t.is_recurring else ""))
                    with st.expander(label):
                        if t.notes:
                            st.caption(f"Notes: {t.notes}")
                        if not t.completed:
                            pet_obj = next(
                                (p for p in owner.pets if p.name == t.pet_name), None)
                            if pet_obj and st.button("Mark complete",
                                                     key=f"done_{t.id}"):
                                pet_obj.complete_task(t.id)
                                if t.is_recurring:
                                    st.success(
                                        f"Done! Next '{t.title}' auto-scheduled.")
                                else:
                                    st.success("Task marked complete.")
                                st.rerun()

# ============================================================
# TAB 3 — Schedule
# ============================================================
with tab_schedule:
    st.subheader("Today's Schedule")

    pending_tasks = [t for t in owner.get_all_tasks() if not t.completed]
    if not pending_tasks:
        st.info("No pending tasks — add some in the Tasks tab.")
    else:
        gen_col, opt_col = st.columns([2, 1])
        with opt_col:
            st.caption("Options")
            show_explanation = st.checkbox("Show reasoning", value=True)
            show_completed   = st.checkbox("Include completed tasks", value=False)

        with gen_col:
            generate = st.button("Generate schedule", type="primary",
                                 use_container_width=True)

        if generate:
            scheduler = Scheduler(owner)
            schedule  = scheduler.generate_schedule()

            if not schedule:
                st.warning("No tasks fit within your available window. "
                           "Try widening your availability or reducing task durations.")
            else:
                # --- Conflict banner (shown first so it's impossible to miss) ---
                conflicts = scheduler.detect_conflicts(schedule)
                if conflicts:
                    st.error(
                        f"⚠ {len(conflicts)} scheduling conflict(s) detected — "
                        "review the highlighted rows below and consider rescheduling."
                    )
                    with st.expander("See conflict details"):
                        for a, b in conflicts:
                            st.write(
                                f"- **{a.task.title}** ({a.start_time.strftime('%H:%M')}–"
                                f"{a.end_time.strftime('%H:%M')}) overlaps with "
                                f"**{b.task.title}** ({b.start_time.strftime('%H:%M')}–"
                                f"{b.end_time.strftime('%H:%M')})"
                            )
                else:
                    st.success("✅ No conflicts — your day is clean!")

                # --- Schedule table ---
                display = schedule
                if show_completed:
                    done_tasks = [t for t in owner.get_all_tasks() if t.completed]
                rows = []
                conflict_titles = {a.task.title for a, b in conflicts} | \
                                  {b.task.title for a, b in conflicts}
                for entry in display:
                    row = entry.to_dict()
                    row["⚠"] = "conflict" if entry.task.title in conflict_titles else ""
                    rows.append(row)

                st.dataframe(rows, use_container_width=True)

                # --- Summary metrics ---
                total_min  = sum(e.task.duration_minutes for e in schedule)
                avail_min  = owner.available_minutes()
                utilisation = round(total_min / avail_min * 100, 1)
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Tasks scheduled", len(schedule))
                m2.metric("Total care time", f"{total_min} min")
                m3.metric("Available time", f"{avail_min} min")
                m4.metric("Day utilisation", f"{utilisation}%")

                # --- Reasoning ---
                if show_explanation:
                    st.subheader("Schedule reasoning")
                    st.code(scheduler.explain_plan(), language=None)

                # --- Skipped tasks ---
                scheduled_ids = {e.task.id for e in schedule}
                skipped = [t for t in pending_tasks
                           if t.id not in scheduled_ids]
                if skipped:
                    with st.expander(f"⏭ {len(skipped)} task(s) skipped "
                                     "(did not fit in window)"):
                        for t in skipped:
                            st.write(f"- **{t.title}** ({t.pet_name}, "
                                     f"{t.duration_minutes} min, {t.priority.value})")
