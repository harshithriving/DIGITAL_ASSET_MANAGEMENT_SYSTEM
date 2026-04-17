import streamlit as st
import requests
import time
from datetime import datetime

API_URL = "http://127.0.0.1:5000"

def safe_json(res):
    try:
        return res.json()
    except:
        return None

def format_bytes(bytes_val):
    if bytes_val < 1024 * 1024:
        return f"{bytes_val / 1024:.1f} KB"
    elif bytes_val < 1024 * 1024 * 1024:
        return f"{bytes_val / (1024 * 1024):.1f} MB"
    else:
        return f"{bytes_val / (1024 * 1024 * 1024):.2f} GB"

def fetch_user_data(employee_id):
    """Fetch user data with retries."""
    for attempt in range(3):
        resp = requests.get(f"{API_URL}/user/{employee_id}")
        if resp.status_code == 200:
            return resp.json()
        time.sleep(0.5)
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

    st.sidebar.info(f"👤 **Your Employee ID:** `{employee_id}`")

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
    user = fetch_user_data(employee_id)
    if user:
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

        # Debug: show raw bytes (remove after fixing)
        st.caption(f"Debug: storage_used = {used_bytes} bytes")
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
            st.write(f"**👨‍💼 Project Manager:** {project.get('project_manager_name', 'Not assigned')}")
            st.divider()

            # Files with comments and version history
            file_res = requests.get(f"{API_URL}/project/files/{project['project_id']}")
            if file_res.status_code == 200:
                files = file_res.json()
                st.subheader("📥 Files")
                if not files:
                    st.info("No files in this project")
                else:
                    for f in files:
                        approved_badge = " ✅ Approved" if f.get('has_approved') else ""
                        total_versions = f.get('total_versions', 0)
                        with st.expander(f"📄 {f['file_name']}{approved_badge} — **Total Versions: {total_versions}**"):
                            # Comments
                            com_res = requests.get(f"{API_URL}/file/comments/{f['file_id']}")
                            if com_res.status_code == 200:
                                comments = com_res.json()
                                if comments:
                                    st.markdown("**Comments:**")
                                    for c in comments:
                                        st.info(f"User {c['user_id']}: {c['comment_text']}")
                                else:
                                    st.caption("No comments yet.")
                            else:
                                st.error("Failed to load comments")

                            # Version history
                            ver_res = requests.get(f"{API_URL}/file/versions/{f['file_id']}")
                            if ver_res.status_code == 200:
                                versions = ver_res.json()
                                if versions:
                                    st.markdown("**Version History:**")
                                    for v in versions:
                                        size_str = format_bytes(v.get('file_size', 0))
                                        uploaded_at = v.get('uploaded_at', '')
                                        if uploaded_at:
                                            try:
                                                dt = datetime.fromisoformat(uploaded_at.replace('Z', '+00:00'))
                                                uploaded_at = dt.strftime("%Y-%m-%d %H:%M")
                                            except:
                                                pass
                                        col_a, col_b = st.columns([10, 2])
                                        with col_a:
                                            st.write(
                                                f"- v{v['version_number']} – **{v['status']}** – {size_str} – "
                                                f"by User {v['uploaded_by']} at {uploaded_at}"
                                            )
                                        with col_b:
                                            if v['uploaded_by'] == employee_id and v['status'] != 'Approved':
                                                if st.button("🗑️", key=f"del_{v['version_id']}"):
                                                    del_res = requests.delete(
                                                        f"{API_URL}/file/version/{v['version_id']}",
                                                        json={"user_id": employee_id}
                                                    )
                                                    if del_res.status_code == 200:
                                                        time.sleep(2)
                                                        updated_user = fetch_user_data(employee_id)
                                                        if updated_user:
                                                            new_used_gb = updated_user["storage_used"] / (1024**3)
                                                            st.success(
                                                                f"✅ Version deleted. "
                                                                f"Storage now: **{new_used_gb:.2f} GB** "
                                                                f"(bytes: {updated_user['storage_used']})"
                                                            )
                                                        else:
                                                            st.success("Version deleted.")
                                                        st.rerun()
                                                    else:
                                                        st.error("Delete failed")
                                else:
                                    st.caption("No version history.")
                            else:
                                st.error("Failed to load version history")
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
                editable_files = [f for f in files if not f.get('has_approved', False)]
                if not editable_files:
                    st.warning("All files in this project have been approved. No further uploads allowed.")
                else:
                    file_options = {f"{f['file_name']} (ID: {f['file_id']})": f['file_id'] for f in editable_files}
                    selected_file_label = st.selectbox("Select file to update", list(file_options.keys()))
                    file_id = file_options[selected_file_label]

                    current_file = next((f for f in editable_files if f['file_id'] == file_id), None)
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
                            time.sleep(1)
                            updated_user = safe_json(requests.get(f"{API_URL}/user/{employee_id}"))
                            if updated_user:
                                new_used_gb = updated_user["storage_used"] / (1024**3)
                                st.success(
                                    f"✅ Simulated version created with size {size_mb} MB. "
                                    f"Storage now: **{new_used_gb:.2f} GB**"
                                )
                            else:
                                st.success("Simulated version created.")
                            st.rerun()
                        elif sim_res.status_code == 400:
                            error_msg = sim_res.json().get("error", "Storage limit exceeded")
                            st.error(f"❌ {error_msg}")
                        else:
                            st.error("Failed to create simulated version")
        else:
            st.error("Failed to load files")