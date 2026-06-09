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
    for attempt in range(3):
        resp = requests.get(f"{API_URL}/user/{employee_id}")
        if resp.status_code == 200:
            return resp.json()
        time.sleep(0.5)
    return None

def get_file_latest_version(file_id):
    resp = requests.get(f"{API_URL}/file/versions/{file_id}")
    if resp.status_code == 200:
        versions = resp.json()
        if versions:
            return versions[0]
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

    # Storage info
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
    else:
        st.error("Failed to load storage data")
    st.divider()

    tab1, tab2 = st.tabs(["📂 Current Project", "📤 Upload New / Edit Files"])

    with tab1:
        selected_name = st.selectbox("Select Project", list(project_map.keys()), key="proj1")
        project = project_map[selected_name]
        with st.expander("📂 Project Details", expanded=True):
            st.write(f"**📌 Project:** {project['project_name']}")
            st.write(f"**📝 Description:** {project['description']}")
            st.write(f"**👨‍💼 Project Manager:** {project.get('project_manager_name', 'Not assigned')}")
            st.divider()

            file_res = requests.get(f"{API_URL}/project/files/{project['project_id']}")
            if file_res.status_code == 200:
                files = file_res.json()
                st.subheader("📥 Files")
                if not files:
                    st.info("No files in this project")
                else:
                    # Categorize files
                    raw_files = []
                    in_process_files = []
                    approved_files = []
                    for f in files:
                        if f.get('has_approved', False):
                            approved_files.append(f)
                        else:
                            latest = get_file_latest_version(f['file_id'])
                            if latest:
                                if latest['status'] == 'Raw':
                                    raw_files.append(f)
                                elif latest['status'] == 'In-Process':
                                    in_process_files.append(f)
                                else:
                                    raw_files.append(f)
                            else:
                                raw_files.append(f)

                    # Helper function to display comments safely
                    def display_comments(file_id):
                        com_res = requests.get(f"{API_URL}/file/comments/{file_id}")
                        if com_res.status_code == 200:
                            comments = com_res.json()
                            if comments:
                                st.markdown("**Comments:**")
                                for c in comments:
                                    # Safe extraction: if 'name' exists use it, else use 'user_id'
                                    if 'name' in c:
                                        commenter = c['name']
                                    elif 'user_id' in c:
                                        commenter = f"User {c['user_id']}"
                                    else:
                                        commenter = "Unknown user"
                                    st.info(f"{commenter}: {c['comment_text']}")
                            else:
                                st.caption("No comments yet.")
                        else:
                            st.error("Failed to load comments")

                    # Raw Files
                    if raw_files:
                        st.markdown("### 📂 Raw Files (Client Uploads)")
                        for f in raw_files:
                            total_versions = f.get('total_versions', 0)
                            with st.expander(f"📄 {f['file_name']} — **Total Versions: {total_versions}**"):
                                raw_res = requests.get(f"{API_URL}/file/raw/{f['file_id']}")
                                if raw_res.status_code == 200:
                                    raw_url = raw_res.json().get('download_url')
                                    st.markdown(f"[⬇ Download Raw File]({raw_url})")
                                else:
                                    st.caption("No raw file available for download")
                                display_comments(f['file_id'])
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
                                            st.write(f"- v{v['version_number']} – **{v['status']}** – {size_str} – by User {v['uploaded_by']} at {uploaded_at}")
                                    else:
                                        st.caption("No version history.")
                                else:
                                    st.error("Failed to load version history")

                    # In-Process Files
                    if in_process_files:
                        st.markdown("### 🔄 In-Process Files (Awaiting Client Review)")
                        for f in in_process_files:
                            total_versions = f.get('total_versions', 0)
                            with st.expander(f"📄 {f['file_name']} — **Total Versions: {total_versions}**"):
                                display_comments(f['file_id'])
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
                                                st.write(f"- v{v['version_number']} – **{v['status']}** – {size_str} – by User {v['uploaded_by']} at {uploaded_at}")
                                            with col_b:
                                                if v == versions[0] and v['uploaded_by'] == employee_id and v['status'] == 'In-Process':
                                                    if st.button("🗑️", key=f"del_{v['version_id']}"):
                                                        del_res = requests.delete(f"{API_URL}/file/version/{v['version_id']}", json={"user_id": employee_id})
                                                        if del_res.status_code == 200:
                                                            time.sleep(2)
                                                            updated_user = fetch_user_data(employee_id)
                                                            if updated_user:
                                                                new_used_gb = updated_user["storage_used"] / (1024**3)
                                                                st.success(f"✅ Version deleted. Storage now: **{new_used_gb:.2f} GB**")
                                                            else:
                                                                st.success("Version deleted.")
                                                            st.rerun()
                                                        else:
                                                            st.error("Delete failed")
                                    else:
                                        st.caption("No version history.")
                                else:
                                    st.error("Failed to load version history")

                    # Approved Files
                    if approved_files:
                        st.markdown("### ✅ Approved Files")
                        for f in approved_files:
                            total_versions = f.get('total_versions', 0)
                            with st.expander(f"📄 {f['file_name']} ✅ Approved — **Total Versions: {total_versions}**"):
                                approved_res = requests.get(f"{API_URL}/file/download/{f['file_id']}")
                                if approved_res.status_code == 200:
                                    approved_url = approved_res.json().get('download_url')
                                    st.markdown(f"[⬇ Download Approved File]({approved_url})")
                                else:
                                    st.caption("No approved version available for download")
                                display_comments(f['file_id'])
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
                                            st.write(f"- v{v['version_number']} – **{v['status']}** – {size_str} – by User {v['uploaded_by']} at {uploaded_at}")
                                    else:
                                        st.caption("No version history.")
                                else:
                                    st.error("Failed to load version history")

            else:
                st.error("Failed to load files")

    # ---------- TAB 2: Upload New / Edit Files (unchanged, keep as before) ----------
    with tab2:
        # ... (keep your existing code for uploads) ...
        st.subheader("📤 Upload New File or Update Existing File")
        selected_name = st.selectbox("Select Project", list(project_map.keys()), key="proj2")
        project = project_map[selected_name]
        folder_res = requests.get(f"{API_URL}/project/full/{project['project_id']}")
        folder_data = safe_json(folder_res)
        if folder_res.status_code == 200 and folder_data:
            folders = folder_data.get("folders", [])
            upload_folders = [f for f in folders if f.get("folder_name") not in ["Root Folder"]]
            folder_map = {f["folder_name"]: f["folder_id"] for f in upload_folders}
            st.markdown("### 📤 Upload New File")
            selected_folder = st.selectbox("Select Folder", list(folder_map.keys()), key="new_file_folder")
            uploaded_file = st.file_uploader("Choose a file to upload", type=None, key="new_file_upload")
            if st.button("📤 Upload New File", key="create_new_file"):
                if uploaded_file is None:
                    st.warning("Please select a file to upload")
                else:
                    with st.spinner(f"Uploading {uploaded_file.name} to {selected_folder}..."):
                        files = {'file': uploaded_file}
                        data = {'folder_id': folder_map[selected_folder], 'uploaded_by': employee_id}
                        upload_res = requests.post(f"{API_URL}/upload-to-imagekit", files=files, data=data)
                    if upload_res.status_code == 201:
                        st.success(f"✅ File '{uploaded_file.name}' uploaded successfully to ImageKit!")
                        st.rerun()
                    else:
                        error_msg = upload_res.json().get('error', 'Unknown error') if upload_res.text else 'Upload failed'
                        st.error(f"Upload failed: {error_msg}")
            st.divider()
            st.markdown("### Update Existing File (Upload New Version)")
            st.caption("You can upload a new version only for files with status 'In-Process'.")
            file_res = requests.get(f"{API_URL}/project/files/{project['project_id']}")
            if file_res.status_code == 200:
                files = file_res.json()
                if not files:
                    st.info("No files in this project to update.")
                else:
                    editable_files = [f for f in files if f.get('has_in_process', False) and not f.get('has_approved', False)]
                    if not editable_files:
                        st.info("All files have been approved. No further uploads are allowed.")
                    else:
                        file_options = {f"{f['file_name']} (ID: {f['file_id']})": f['file_id'] for f in editable_files}
                        selected_file_label = st.selectbox("Select file to update", list(file_options.keys()), key="update_file")
                        file_id = file_options[selected_file_label]
                        new_version_file = st.file_uploader("Choose new version file", type=None, key="version_file")
                        if new_version_file and st.button("🚀 Submit New Version", key="submit_version"):
                            with st.spinner(f"Uploading new version of {new_version_file.name}..."):
                                files = {'file': new_version_file}
                                data = {'file_id': file_id, 'uploaded_by': employee_id}
                                upload_res = requests.post(f"{API_URL}/upload-version-to-imagekit", files=files, data=data)
                            if upload_res.status_code == 201:
                                st.success("✅ New version uploaded. It is now under client review.")
                                time.sleep(1)
                                updated_user = fetch_user_data(employee_id)
                                if updated_user:
                                    new_used_gb = updated_user["storage_used"] / (1024**3)
                                    st.info(f"Storage automatically updated to **{new_used_gb:.2f} GB** via trigger.")
                                st.rerun()
                            else:
                                error_msg = upload_res.json().get('error', 'Unknown error') if upload_res.text else 'Upload failed'
                                st.error(f"Upload failed: {error_msg}")
            else:
                st.error("Failed to load files")
        else:
            st.error("Failed to load folder structure")

    # Simulated upload expander (unchanged)
    with st.expander("🧪 Simulated Upload (for trigger demonstration)"):
        # ... (keep your existing simulated upload code) ...
        st.caption("Creates a simulated version without an actual file, demonstrating storage and version count triggers.")
        selected_name = st.selectbox("Select Project", list(project_map.keys()), key="sim_proj")
        project = project_map[selected_name]
        file_res = requests.get(f"{API_URL}/project/files/{project['project_id']}")
        if file_res.status_code == 200:
            files = file_res.json()
            editable_files = [f for f in files if not f.get('has_approved', False)]
            if editable_files:
                file_options = {f"{f['file_name']} (ID: {f['file_id']})": f['file_id'] for f in editable_files}
                selected_file_label = st.selectbox("Select file", list(file_options.keys()), key="sim_file")
                file_id = file_options[selected_file_label]
                size_mb = st.number_input("Simulated size (MB)", min_value=0.0, value=1.0, step=0.5, key="sim_size")
                if st.button("Simulate Upload", key="sim_button"):
                    size_bytes = int(size_mb * 1024 * 1024)
                    sim_res = requests.post(
                        f"{API_URL}/simulate/upload/version",
                        json={"file_id": file_id, "uploaded_by": employee_id, "file_size": size_bytes}
                    )
                    if sim_res.status_code == 201:
                        st.success(f"Simulated version of {size_mb} MB created. Check the version history.")
                        st.rerun()
                    else:
                        st.error("Failed")
            else:
                st.info("No files available for simulation.")

if __name__ == "__main__":
    # This is not the main entry point; the app uses the function above.
    pass