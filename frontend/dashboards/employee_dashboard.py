import streamlit as st
import requests
import time

API_URL = "http://127.0.0.1:5000"

def safe_json(res):
    try:
        return res.json()
    except:
        return None

def show_employee_dashboard():
    col1, col2 = st.columns([8, 1])
    with col2:
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.role = None
            st.session_state.user_id = None
            st.rerun()

    st.title("🧑‍💻 Employee Dashboard")

    employee_id = st.session_state.user_id
    if not employee_id:
        st.error("User ID not found")
        return

    # Get assigned projects
    res = requests.get(f"{API_URL}/employee/projects/{employee_id}")
    if res.status_code != 200:
        st.error("Failed to load projects")
        return
    projects = res.json()
    if not projects:
        st.info("No assigned projects")
        return
    project_map = {p["project_name"]: p for p in projects}

    # --- Storage Info (Live) ---
    user_res = requests.get(f"{API_URL}/user/{employee_id}")
    if user_res.status_code == 200:
        user = user_res.json()
        used_bytes = user["storage_used"]
        limit_bytes = user["storage_limit"]
        used_gb = used_bytes / (1024**3)
        limit_gb = limit_bytes / (1024**3)
        left_gb = limit_gb - used_gb

        col1, col2, col3 = st.columns([6, 2, 2])
        col1.metric("💾 Storage Used", f"{used_gb:.2f} GB")
        col2.metric("📦 Storage Left", f"{left_gb:.2f} GB / {limit_gb:.2f} GB")
        with col3:
            if st.button("🔄 Refresh Storage"):
                st.rerun()

        percent = used_gb / limit_gb if limit_gb else 0
        if percent > 1:
            st.warning("⚠️ Storage limit exceeded! Please free up space.")
            percent = 1.0
        st.progress(percent)
    else:
        st.error("Failed to load storage data")
    st.divider()

    tab1, tab2 = st.tabs(["📂 Current Project", "📤 Upload Edited File (Simulated)"])

    with tab1:
        selected_name = st.selectbox("Select Project", list(project_map.keys()), key="proj1")
        project = project_map[selected_name]
        with st.expander("📂 Project Details", expanded=True):
            st.write(f"**📌 Project:** {project['project_name']}")
            st.write(f"**📝 Description:** {project['description']}")
            st.write(f"**👨‍💼 PM:** {project['project_manager_user_id']}")
            st.divider()

            # Files with comments
            file_res = requests.get(f"{API_URL}/project/files/{project['project_id']}")
            if file_res.status_code == 200:
                files = file_res.json()
                st.subheader("📥 Files")
                if not files:
                    st.info("No files in this project")
                else:
                    for f in files:
                        st.markdown(f"**📄 {f['file_name']}**")
                        com_res = requests.get(f"{API_URL}/file/comments/{f['file_id']}")
                        if com_res.status_code == 200:
                            comments = com_res.json()
                            if comments:
                                st.markdown("Comments:")
                                for c in comments:
                                    st.info(f"User {c['user_id']}: {c['comment_text']}")
                            else:
                                st.caption("No comments yet.")
                        else:
                            st.error("Failed to load comments")
                        st.markdown("---")
            else:
                st.error("Failed to load files")

    with tab2:
        st.subheader("📤 Upload Edited File (Simulated)")
        st.caption("Enter file size in MB. After upload, storage will update automatically via database trigger.")

        selected_name = st.selectbox("Select Project", list(project_map.keys()), key="proj2")
        project = project_map[selected_name]

        file_res = requests.get(f"{API_URL}/project/files/{project['project_id']}")
        if file_res.status_code == 200:
            files = file_res.json()
            if not files:
                st.info("No files in this project to update.")
            else:
                file_options = {f"{f['file_name']} (ID: {f['file_id']})": f['file_id'] for f in files}
                selected_file_label = st.selectbox("Select file to update", list(file_options.keys()))
                file_id = file_options[selected_file_label]

                current_file = next((f for f in files if f['file_id'] == file_id), None)
                default_name = current_file['file_name'] if current_file else ""

                new_file_name = st.text_input("New file name (optional)", value=default_name)

                size_mb = st.number_input("File size (MB) for this version", min_value=0.0, value=1.0, step=0.5)
                size_bytes = int(size_mb * 1024 * 1024)

                if st.button("🚀 Submit Simulated Version"):
                    sim_res = requests.post(
                        f"{API_URL}/simulate/upload/version",
                        json={
                            "file_id": file_id,
                            "uploaded_by": employee_id,
                            "file_name": new_file_name,
                            "file_size": size_bytes
                        }
                    )
                    if sim_res.status_code == 201:
                        # Give the database trigger a moment to update
                        time.sleep(1)
                        # Fetch updated user data
                        updated_user = safe_json(requests.get(f"{API_URL}/user/{employee_id}"))
                        if updated_user:
                            new_used_gb = updated_user["storage_used"] / (1024**3)
                            st.success(
                                f"✅ Simulated version created with size {size_mb} MB. "
                                f"**Database trigger** automatically updated your storage to **{new_used_gb:.2f} GB**."
                            )
                        else:
                            st.success("Simulated version created.")
                        # Rerun to refresh the entire dashboard
                        st.rerun()
                    else:
                        st.error("Failed to create simulated version")
        else:
            st.error("Failed to load files")