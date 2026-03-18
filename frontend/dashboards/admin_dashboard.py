import streamlit as st
import pandas as pd


# ==============================
# STORAGE CALCULATION FUNCTION
# ==============================
def calculate_storage():
    TOTAL_LIMIT_MB = 5000  # Admin system limit

    total_bytes = 0

    if "projects" in st.session_state:
        for project in st.session_state.projects.values():

            # RAW Files
            for category in project["RAW Files"].values():
                for f in category:
                    total_bytes += f.size

            # Edited Files
            for f in project["Edited Files"]:
                total_bytes += f.size

    used_mb = total_bytes / (1024 * 1024)
    left_mb = TOTAL_LIMIT_MB - used_mb

    return round(used_mb, 2), round(left_mb, 2), TOTAL_LIMIT_MB


# ==============================
# ADMIN DASHBOARD
# ==============================
def show_admin_dashboard():

    st.title("🛠 Admin Dashboard")

    col1, col2 = st.columns([8, 1])

    with col2:
        st.markdown("###")
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.role = None
            st.rerun()

    # ==============================
    # 💾 STORAGE OVERVIEW
    # ==============================
    used, left, total = calculate_storage()

    col1, col2 = st.columns(2)

    with col1:
        st.metric("💾 Total Storage Used", f"{used} MB")

    with col2:
        st.metric("📦 Storage Remaining", f"{left} MB / {total} MB")

    # Progress bar
    percent = used / total if total != 0 else 0
    st.progress(percent)

    # Status indicator
    if percent < 0.5:
        st.success("🟢 System healthy")
    elif percent < 0.8:
        st.warning("🟡 Moderate usage")
    else:
        st.error("🔴 Storage nearly full")

    st.divider()

    # ==============================
    # TABS
    # ==============================
    tab1, tab2, tab3 = st.tabs(
        ["📂 Assign Projects", "👥 Users & Storage", "🚀 Running Projects"]
    )

    # ==============================
    # TAB 1 — ASSIGN PROJECTS
    # ==============================

    with tab1:
        st.subheader("📦 Pending Client Projects")

        # If no projects exist
        if "projects" not in st.session_state or not st.session_state.projects:
            st.info("No projects available")
        else:

            project_names = list(st.session_state.projects.keys())

            selected_project = st.selectbox(
                "Select Project",
                project_names
            )

            project = st.session_state.projects[selected_project]

            st.divider()

            # ==============================
            # 📌 PROJECT DETAILS
            # ==============================
            st.subheader("📌 Project Details")

            st.write(f"**Project Name:** {selected_project}")
            st.write(f"**Description:** {project['description']}")
            st.write(f"**Created On:** {project['created_at']}")

            st.divider()

            # ==============================
            # 📂 FILE SUMMARY
            # ==============================
            st.subheader("📂 Files Overview")

            raw = project["RAW Files"]

            for category in raw:
                st.write(f"**{category}:** {len(raw[category])} files")

            st.write(f"**Edited Files:** {len(project['Edited Files'])}")

            st.divider()

            # ==============================
            # 🎯 ASSIGN TO PM
            # ==============================
            col1, col2 = st.columns([2, 1])

            with col1:
                st.subheader("🎯 Assign Project")

                pm_list = ["Ashwini", "Priya", "Vikram"]

                selected_pm = st.selectbox(
                    "Assign to Project Manager",
                    pm_list
                )

                if st.button("✅ Assign Project", use_container_width=True):

                    # Save assignment
                    project["assigned_pm"] = selected_pm
                    project["status"] = "Assigned"

                    st.success(f"{selected_project} assigned to {selected_pm}")

            # ==============================
            # 👨‍💼 PM STATUS PANEL
            # ==============================
            with col2:
                st.subheader("👨‍💼 PM Status")

                for pm in pm_list:
                    assigned_count = sum(
                        1 for p in st.session_state.projects.values()
                        if p.get("assigned_pm") == pm
                    )

                    st.write(f"{pm}: {assigned_count} projects")




    

    # ==============================
    # TAB 2 — USERS
    # ==============================
    with tab2:
        st.subheader("👥 Users & Storage Usage")

        users = pd.DataFrame({
            "Name": ["Ashwini", "Rahul", "Client A"],
            "Role": ["PM", "Employee", "Client"],
            "Storage Used": ["2.1 GB", "5.4 GB", "1.2 GB"]
        })

        st.dataframe(users, use_container_width=True)

    # ==============================
    # TAB 3 — RUNNING PROJECTS
    # ==============================
    with tab3:
        st.subheader("🚀 Active Projects")

        running = pd.DataFrame({
            "Project": ["Ad Campaign", "Brand Video"],
            "PM": ["Ashwini", "Vikram"],
            "Status": ["In Progress", "Review Phase"]
        })

        st.dataframe(running, use_container_width=True)