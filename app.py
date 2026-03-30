"""
app.py — PawPal+ Streamlit UI.

Wires the Owner / Pet / Task / Scheduler backend into an interactive app.
Session state acts as the app's persistent memory so objects survive reruns.
"""

import streamlit as st
from pawpal_system import Owner, Pet, Task, TaskType, Priority, Scheduler

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")

# ---------------------------------------------------------------------------
# Session-state initialisation
# Each key is created exactly once; subsequent reruns skip the if-block.
# ---------------------------------------------------------------------------
if "owner" not in st.session_state:
    st.session_state.owner = None          # set when the owner form is submitted

# ---------------------------------------------------------------------------
# Step 1 — Create the owner (shown only until one exists)
# ---------------------------------------------------------------------------
if st.session_state.owner is None:
    st.subheader("Welcome! Let's get you set up.")
    with st.form("owner_form"):
        owner_name   = st.text_input("Your name", value="Jordan")
        avail_start  = st.text_input("Available from (HH:MM)", value="08:00")
        avail_end    = st.text_input("Available until (HH:MM)", value="20:00")
        submitted    = st.form_submit_button("Create profile")

    if submitted and owner_name.strip():
        st.session_state.owner = Owner(
            name=owner_name.strip(),
            available_start=avail_start,
            available_end=avail_end,
        )
        st.rerun()
    st.stop()   # nothing else renders until an owner exists

owner: Owner = st.session_state.owner

# ---------------------------------------------------------------------------
# Sidebar — owner summary
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header(f"Owner: {owner.name}")
    st.caption(f"Available {owner.available_start} – {owner.available_end} "
               f"({owner.available_minutes()} min/day)")
    st.metric("Pets", len(owner.pets))
    st.metric("Total tasks", len(owner.get_all_tasks()))

# ---------------------------------------------------------------------------
# Tab layout
# ---------------------------------------------------------------------------
tab_pets, tab_tasks, tab_schedule = st.tabs(["Pets", "Tasks", "Schedule"])

# ============================================================
# TAB 1 — Pets
# ============================================================
with tab_pets:
    st.subheader("Your pets")

    # --- Add pet form ---
    with st.expander("Add a new pet", expanded=len(owner.pets) == 0):
        with st.form("add_pet_form"):
            col1, col2 = st.columns(2)
            with col1:
                pet_name  = st.text_input("Pet name")
                species   = st.selectbox("Species", ["dog", "cat", "rabbit", "bird", "other"])
            with col2:
                age       = st.number_input("Age (years)", min_value=0.0, max_value=30.0,
                                            step=0.5, value=1.0)
                breed     = st.text_input("Breed (optional)")
            add_pet = st.form_submit_button("Add pet")

        if add_pet:
            if not pet_name.strip():
                st.warning("Please enter a pet name.")
            elif any(p.name == pet_name.strip() for p in owner.pets):
                st.warning(f"'{pet_name}' is already registered.")
            else:
                owner.add_pet(Pet(name=pet_name.strip(), species=species,
                                  age=age, breed=breed))
                st.success(f"{pet_name} added!")
                st.rerun()

    # --- Pet list ---
    if not owner.pets:
        st.info("No pets yet. Add one above.")
    else:
        for pet in owner.pets:
            with st.expander(f"{pet.name}  ({pet.species}, {pet.age}y{', ' + pet.breed if pet.breed else ''})"):
                st.caption(f"{len(pet.tasks)} task(s) registered")
                if pet.tasks:
                    st.table([t.to_dict() for t in pet.tasks])
                if st.button(f"Remove {pet.name}", key=f"del_pet_{pet.name}"):
                    owner.remove_pet(pet.name)
                    st.rerun()

# ============================================================
# TAB 2 — Tasks
# ============================================================
with tab_tasks:
    st.subheader("Add a task")

    if not owner.pets:
        st.info("Add a pet first before creating tasks.")
    else:
        with st.form("add_task_form"):
            col1, col2 = st.columns(2)
            with col1:
                pet_choice   = st.selectbox("Assign to pet",
                                            [p.name for p in owner.pets])
                task_title   = st.text_input("Task title", value="Morning walk")
                task_type    = st.selectbox("Type",
                                            [t.value for t in TaskType])
                priority_val = st.selectbox("Priority",
                                            [p.value for p in Priority],
                                            index=1)
            with col2:
                duration     = st.number_input("Duration (minutes)", min_value=1,
                                               max_value=480, value=20)
                has_time     = st.checkbox("Set a specific time")
                sched_hour   = st.number_input("Hour (0-23)", min_value=0,
                                               max_value=23, value=8,
                                               disabled=not has_time)
                sched_min    = st.number_input("Minute", min_value=0,
                                               max_value=59, value=0,
                                               disabled=not has_time)
                is_recurring = st.checkbox("Recurring?")
                recur_hours  = st.number_input("Repeat every N hours",
                                               min_value=1, max_value=48, value=24,
                                               disabled=not is_recurring)
            notes = st.text_input("Notes (optional)")
            add_task = st.form_submit_button("Add task")

        if add_task:
            from datetime import datetime
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
            st.success(f"Task '{new_task.title}' added to {pet_choice}.")
            st.rerun()

    # --- All tasks overview ---
    all_tasks = owner.get_all_tasks()
    if all_tasks:
        st.subheader("All tasks")
        st.table([t.to_dict() for t in all_tasks])

# ============================================================
# TAB 3 — Schedule
# ============================================================
with tab_schedule:
    st.subheader("Today's Schedule")

    if not owner.get_all_tasks():
        st.info("Add some tasks first, then generate a schedule.")
    else:
        if st.button("Generate schedule"):
            scheduler = Scheduler(owner)
            schedule  = scheduler.generate_schedule()

            if not schedule:
                st.warning("No tasks fit within your available window today.")
            else:
                # Typed table
                st.table([e.to_dict() for e in schedule])

                # Plain-text explanation
                st.subheader("Plan explanation")
                st.code(scheduler.explain_plan(), language=None)

                # Conflict warnings
                conflicts = scheduler.detect_conflicts(schedule)
                if conflicts:
                    st.error(f"{len(conflicts)} scheduling conflict(s) detected:")
                    for a, b in conflicts:
                        st.write(f"- '{a.task.title}' overlaps with '{b.task.title}'")
                else:
                    st.success("No conflicts — your day is clean!")
