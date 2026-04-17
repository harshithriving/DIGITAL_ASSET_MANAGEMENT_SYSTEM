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

    # Create tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📂 Assign Projects",
        "👥 Users & Storage",
        "🚀 Running Projects",
        "📋 Audit Log"
    ])

    # ---------- Tab 1: Assign Projects ----------
    with tab1:
        st.subheader("📦 Projects")
        response = requests.get(f"{API_URL}/projects")
        if response.status_code == 200:
            projects = response.json()
            if not projects:
                st.info("No projects found")
            else:
                # Sort projects by created_at descending (latest first)
                projects.sort(key=lambda x: x.get('created_at', ''), reverse=True)
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

    # ---------- Tab 2: Users & Storage ----------
    # ---------- Tab 2: Users & Storage ----------
    with tab2:
        st.subheader("👥 Users & Storage")
        
        # Fetch storage data
        storage_response = requests.get(f"{API_URL}/all_users_storage")
        # Fetch full user data (includes user_id)
        users_response = requests.get(f"{API_URL}/users/Employee")  # This returns user_id and name
        # Also fetch other roles if needed
        all_users_response = requests.get(f"{API_URL}/users/Admin")  # You'll need similar for all roles
        
        if storage_response.status_code == 200 and users_response.status_code == 200:
            storage_data = storage_response.json()
            employee_data = users_response.json()
            
            # Create a mapping of name to storage info
            user_map = {}
            for u in storage_data:
                user_map[u["name"]] = u
            
            # Build complete user list with user_id from employee_data
            users = []
            for emp in employee_data:
                if emp["name"] in user_map:
                    user_info = user_map[emp["name"]]
                    user_info["user_id"] = emp["user_id"]
                    users.append(user_info)
            
            # Fetch project count for each employee
            for u in users:
                if u["role"] == "Employee":
                    count_res = requests.get(f"{API_URL}/employee/project_count/{u['user_id']}")
                    if count_res.status_code == 200:
                        u["projects_assigned"] = count_res.json().get("project_count", 0)
                    else:
                        u["projects_assigned"] = "Error"
                else:
                    u["projects_assigned"] = "N/A"
            
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
                "storage_limit": "storage_limit_bytes",
                "projects_assigned": "projects_assigned"
            })
            # Select and order columns
            display_cols = ['name', 'role', 'storage_used (GB)', 'storage_limit (GB)', 'projects_assigned']
            available_cols = [col for col in display_cols if col in df.columns]
            st.dataframe(df[available_cols], use_container_width=True)
            
            # Show warning if any employee has >2 projects
            over_assigned = df[df['role'] == 'Employee'][df['projects_assigned'] > 2]
            if not over_assigned.empty:
                st.warning("⚠️ Some employees are assigned to more than 2 projects (violates policy)!")
        else:
            st.error("Failed to load users")

    # ---------- Tab 3: Running Projects ----------
    with tab3:
        st.subheader("🚀 Active Projects")
        response = requests.get(f"{API_URL}/projects")
        if response.status_code == 200:
            projects = response.json()
            # Sort projects by created_at descending (latest first)
            projects.sort(key=lambda x: x.get('created_at', ''), reverse=True)
            running = [
                {
                    "Project": p["project_name"],
                    "PM": p["project_manager_user_id"],
                    "Status": "In Progress" if p["project_manager_user_id"] else "Unassigned",
                    "Created": p.get("created_at", "")[:10] if p.get("created_at") else ""
                }
                for p in projects
            ]
            st.dataframe(pd.DataFrame(running), use_container_width=True)
        else:
            st.error("Failed to load projects")

    # ---------- Tab 4: Audit Log ----------
    with tab4:
        st.subheader("📋 File Status Change Log")
        logs_res = requests.get(f"{API_URL}/audit/logs")
        if logs_res.status_code == 200:
            logs = logs_res.json()
            if logs:
                # Convert to DataFrame for nice display
                df_logs = pd.DataFrame(logs)
                # Format datetime
                if 'changed_at' in df_logs.columns:
                    df_logs['changed_at'] = pd.to_datetime(df_logs['changed_at'])
                # Select and order columns
                display_cols = ['file_name', 'old_status', 'new_status', 'changed_by_name', 'changed_at']
                # Ensure all columns exist
                available_cols = [col for col in display_cols if col in df_logs.columns]
                st.dataframe(df_logs[available_cols], use_container_width=True)
                
                # Optional: show raw JSON expander
                with st.expander("View Raw Log Data"):
                    st.json(logs)
            else:
                st.info("No status changes have been logged yet. Approve or reject a file to see entries here.")
        else:
            st.error("Failed to load audit logs")
            if logs_res.text:
                st.write("Error details:", logs_res.text)