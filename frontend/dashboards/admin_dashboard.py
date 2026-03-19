import streamlit as st
import pandas as pd
import requests

API_URL = "http://127.0.0.1:5000"

def show_admin_dashboard():
    st.title("🛠 Admin Dashboard")
    col1, col2 = st.columns([8, 1])
    with col2:
        st.markdown("###")
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.role = None
            st.session_state.user_id = None
            st.rerun()

    # Storage summary
    response = requests.get(f"{API_URL}/all_users_storage")
    if response.status_code == 200:
        users = response.json()
        total_used = sum(u["storage_used"] for u in users)
        total_limit = sum(u["storage_limit"] for u in users)
        col1, col2 = st.columns(2)
        with col1:
            st.metric("💾 Total Storage Used", f"{total_used / (1024**3):.2f} GB")
        with col2:
            st.metric("📦 Total Capacity", f"{total_limit / (1024**3):.2f} GB")
        percent = total_used / total_limit if total_limit else 0
        if percent > 1:
            st.warning("⚠️ Overall storage limit exceeded!")
            percent = 1.0
        st.progress(percent)
    else:
        st.error("Failed to load storage data")
    st.divider()

    tab1, tab2, tab3 = st.tabs(["📂 Assign Projects", "👥 Users & Storage", "🚀 Running Projects"])

    with tab1:
        st.subheader("📦 Projects")
        response = requests.get(f"{API_URL}/projects")
        if response.status_code == 200:
            projects = response.json()
            if not projects:
                st.info("No projects found")
            else:
                df = pd.DataFrame(projects)
                st.dataframe(df, use_container_width=True)
                project_map = {p["project_name"]: p for p in projects}
                selected_name = st.selectbox("Select Project", list(project_map.keys()))
                selected_project = project_map[selected_name]

                st.divider()
                st.subheader("📌 Project Details")
                st.write(f"**Name:** {selected_project['project_name']}")
                st.write(f"**Description:** {selected_project['description']}")

                # Fetch PMs
                pm_res = requests.get(f"{API_URL}/users/ProjectManager")
                if pm_res.status_code == 200:
                    pms = pm_res.json()
                    if pms:
                        pm_names = [pm["name"] for pm in pms]
                        pm_map = {pm["name"]: pm["user_id"] for pm in pms}
                        selected_pm_name = st.selectbox("Select PM", pm_names)
                        if st.button("✅ Assign Project"):
                            data = {
                                "project_id": selected_project["project_id"],
                                "pm_user_id": pm_map[selected_pm_name]
                            }
                            res = requests.post(f"{API_URL}/assign_project", json=data)
                            if res.status_code == 200:
                                st.success("Project assigned successfully")
                            else:
                                st.error("Assignment failed")
                    else:
                        st.warning("No project managers available")
                else:
                    st.error("Failed to load PMs")
        else:
            st.error("Failed to load projects")

    with tab2:
        st.subheader("👥 Users & Storage")
        response = requests.get(f"{API_URL}/all_users_storage")
        if response.status_code == 200:
            users = response.json()
            # Convert bytes to GB for display
            for u in users:
                u["storage_used_gb"] = u["storage_used"] / (1024**3)
                u["storage_limit_gb"] = u["storage_limit"] / (1024**3)
            df = pd.DataFrame(users)
            # Rename columns for clarity
            df = df.rename(columns={
                "storage_used_gb": "storage_used (GB)",
                "storage_limit_gb": "storage_limit (GB)",
                "storage_used": "storage_used_bytes",
                "storage_limit": "storage_limit_bytes"
            })
            st.dataframe(df, use_container_width=True)
        else:
            st.error("Failed to load users")

    with tab3:
        st.subheader("🚀 Active Projects")
        response = requests.get(f"{API_URL}/projects")
        if response.status_code == 200:
            projects = response.json()
            running = [
                {
                    "Project": p["project_name"],
                    "PM": p["project_manager_user_id"],
                    "Status": "In Progress" if p["project_manager_user_id"] else "Unassigned"
                }
                for p in projects
            ]
            st.dataframe(pd.DataFrame(running), use_container_width=True)
        else:
            st.error("Failed to load projects")

            