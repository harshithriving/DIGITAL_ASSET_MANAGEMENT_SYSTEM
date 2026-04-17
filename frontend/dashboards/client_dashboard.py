import streamlit as st
import requests

API_URL = "http://127.0.0.1:5000"

def safe_json(res):
    try:
        return res.json()
    except:
        return None

def show_client_dashboard():
    if not st.session_state.get("user_id"):
        st.error("User not logged in properly")
        return

    col1, col2 = st.columns([8, 1])
    with col2:
        if st.button("🚪 Logout"):
            st.session_state.role = None
            st.session_state.user_id = None
            st.rerun()

    st.title("👤 Client Dashboard")
    menu = st.sidebar.radio("Menu", ["📁 My Projects", "➕ Create Project"])

    if menu == "➕ Create Project":
        st.subheader("➕ Create New Project")
        project_name = st.text_input("Project Name")
        description = st.text_area("Project Description")

        st.markdown("**Add Initial Files (optional)**")
        st.caption("Format: `filename.ext, size_in_MB` (one per line). Example: `video.mp4, 5` (5 MB)")

        col1, col2 = st.columns(2)
        with col1:
            videos_input = st.text_area("📹 Videos", height=150, 
                placeholder="video1.mp4, 5\nintro.mov, 10")
            images_input = st.text_area("🖼️ Images", height=150,
                placeholder="logo.png, 2\nbanner.jpg, 3")
        with col2:
            audio_input = st.text_area("🎵 Audio", height=150,
                placeholder="sound.mp3, 1\nvoice.wav, 0.5")
            others_input = st.text_area("📄 Others", height=150,
                placeholder="document.pdf, 2.5\narchive.zip, 5")

        if st.button("Create Project"):
            if not project_name:
                st.error("Project name required")
                return

            # Create project
            with st.spinner("Creating project..."):
                res = requests.post(
                    f"{API_URL}/client/projects",
                    json={
                        "project_name": project_name,
                        "description": description,
                        "client_user_id": st.session_state.user_id
                    }
                )
            data = safe_json(res)
            if not data or "project_id" not in data:
                st.error("Project creation failed")
                if res.text:
                    st.write(res.text)
                return

            project_id = data["project_id"]
            st.success(f"✅ Project '{project_name}' created with ID {project_id}")

            # Get folder IDs
            struct_res = requests.get(f"{API_URL}/project/full/{project_id}")
            struct_data = safe_json(struct_res)
            if not struct_data:
                st.warning("Could not retrieve folder structure; files not created.")
                return

            folders = struct_data.get("folders", [])
            folder_map = {f["folder_name"]: f["folder_id"] for f in folders}

            folder_inputs = {
                "Videos": videos_input,
                "Images": images_input,
                "Audio": audio_input,
                "Others": others_input
            }

            created_counts = {}
            error_files = []
            with st.spinner("Creating files..."):
                for folder_name, input_text in folder_inputs.items():
                    if folder_name not in folder_map:
                        st.warning(f"Folder '{folder_name}' not found, skipping.")
                        continue
                    folder_id = folder_map[folder_name]
                    lines = [line.strip() for line in input_text.split("\n") if line.strip()]
                    count = 0
                    for line in lines:
                        parts = line.split(",")
                        if len(parts) != 2:
                            error_files.append(f"Invalid format in {folder_name}: '{line}'")
                            continue
                        fname = parts[0].strip()
                        size_str = parts[1].strip()
                        if not fname or not size_str:
                            error_files.append(f"Missing name or size in {folder_name}: '{line}'")
                            continue
                        try:
                            size_mb = float(size_str)
                            size_bytes = int(size_mb * 1024 * 1024)   # Convert MB → bytes
                        except ValueError:
                            error_files.append(f"Invalid size in {folder_name}: '{size_str}'")
                            continue

                        create_res = requests.post(
                        f"{API_URL}/file/create",
                        json={
                            "file_name": fname,
                            "folder_id": folder_id,
                            "user_id": st.session_state.user_id,
                            "file_size": size_bytes
                        }
                    )
                    if create_res.status_code == 201:
                        count += 1
                    elif create_res.status_code == 400:
                        error_msg = create_res.json().get("error", "Storage limit exceeded")
                        error_files.append(f"Storage error for {fname} in {folder_name}: {error_msg}")
                        break  # Stop creating more files for this project
                    else:
                        error_files.append(f"Failed to create {fname} in {folder_name}")
                        
                    created_counts[folder_name] = count

            if any(created_counts.values()):
                st.success("Files created successfully:")
                for folder, count in created_counts.items():
                    if count:
                        st.write(f"- {folder}: {count} file(s)")
            if error_files:
                st.error("Errors encountered:")
                for err in error_files:
                    st.write(f"- {err}")
            if not any(created_counts.values()) and not error_files:
                st.info("No files were added.")

            if st.button("View Project Now"):
                st.session_state["selected_project_id"] = project_id
                st.info("Switch to 'My Projects' and select the project to view files.")

    elif menu == "📁 My Projects":
        res = requests.get(
            f"{API_URL}/client/projects",
            params={"client_id": st.session_state.user_id}
        )
        projects = safe_json(res)
        if not projects:
            st.info("No projects")
            return

        selected_project = st.selectbox(
            "Select Project",
            projects,
            format_func=lambda x: f"{x['project_name']} (Created: {x['created_at'][:10]})"
            # format_func=lambda x: f"{x['project_name']} (ID: {x['project_id']})"
        )
        project_id = selected_project["project_id"]

        st.subheader("📌 Project Info")
        st.write(selected_project["description"])

                # Team info
        st.subheader("👥 Team")
        pm_name = selected_project.get("project_manager_name", "Not assigned")
        st.write(f"**Project Manager:** {pm_name}")
        emp_res = requests.get(f"{API_URL}/project/employees/{project_id}")
        if emp_res.status_code == 200:
            employees = emp_res.json()
            if employees:
                st.write("**Employees:**")
                for emp in employees:
                    st.write(f"- {emp['name']}")
            else:
                st.write("No employees assigned yet.")
        else:
            st.error("Failed to load employees")
        st.divider()

        # Files under review (unchanged)
        st.subheader("📝 Files Under Review")
        review = safe_json(requests.get(f"{API_URL}/file/review/{project_id}")) or []
        if not review:
            st.info("No files under review")
        else:
            for f in review:
                st.write(f"📄 {f['file_name']} (V{f['version_number']})")
                col1, col2 = st.columns(2)
                if col1.button("Approve", key=f"a_{f['version_id']}"):
                    requests.put(f"{API_URL}/file/approve/{f['version_id']}")
                    st.rerun()
                if col2.button("Reject", key=f"r_{f['version_id']}"):
                    requests.put(f"{API_URL}/file/reject/{f['version_id']}")
                    st.rerun()
                comment = st.text_input("Add improvement suggestion", key=f"comm_{f['version_id']}")
                if st.button("Submit Comment", key=f"btn_{f['version_id']}"):
                    if comment:
                        file_id = f.get('file_id')
                        if file_id:
                            requests.post(
                                f"{API_URL}/comments",
                                json={
                                    "comment": comment,
                                    "file_id": file_id,
                                    "user_id": st.session_state.user_id
                                }
                            )
                            st.rerun()
                st.markdown("---")
        st.divider()

        # Project structure
        st.subheader("📂 Project Structure")
        res = requests.get(f"{API_URL}/project/full/{project_id}")
        data = safe_json(res)
        if not data:
            st.warning("No structure found")
            return

        folders = data.get("folders", [])
        files = data.get("files", [])

        if not folders:
            st.warning("No folders found")
            return

        # Add new file (size in MB → bytes)
        st.markdown("### ➕ Add New File")
        folder_map = {f["folder_name"]: f["folder_id"] for f in folders}
        new_file_name = st.text_input("File Name")
        new_file_size_mb = st.number_input("File size (MB)", min_value=0.0, value=1.0, step=0.5, key="new_file_size")
        new_file_size_bytes = int(new_file_size_mb * 1024 * 1024)
        selected_folder = st.selectbox("Select Folder", list(folder_map.keys()))
        if st.button("Create File"):
            if not new_file_name:
                st.warning("Enter file name")
            else:
                create_res = requests.post(
                    f"{API_URL}/file/create",
                    json={
                        "file_name": new_file_name,
                        "folder_id": folder_map[selected_folder],
                        "user_id": st.session_state.user_id,
                        "file_size": new_file_size_bytes
                    }
                )
                if create_res.status_code == 201:
                    st.success(f"File created with size {new_file_size_mb} MB")
                    st.rerun()
                elif create_res.status_code == 400:
                    error_msg = create_res.json().get("error", "Storage limit exceeded")
                    st.error(f"❌ {error_msg}")
                else:
                    st.error("Failed")
                st.divider()

        # Tree view (unchanged)
        folder_map_full = {f["folder_id"]: f for f in folders}
        children = {}
        for f in folders:
            children.setdefault(f["parent_folder_id"], []).append(f)

        def show_folder(fid):
            folder = folder_map_full[fid]
            with st.expander(f"📁 {folder['folder_name']}"):
                folder_files = [f for f in files if f["folder_id"] == fid]
                for file in folder_files:
                    with st.expander(f"📄 {file['file_name']}"):
                        comments = safe_json(requests.get(f"{API_URL}/file/comments/{file['file_id']}")) or []
                        for c in comments:
                            st.info(f"User {c['user_id']}: {c['comment_text']}")
                        comment = st.text_input("Add comment", key=f"c_{file['file_id']}")
                        if st.button("Submit", key=f"s_{file['file_id']}"):
                            requests.post(
                                f"{API_URL}/comments",
                                json={
                                    "comment": comment,
                                    "file_id": file["file_id"],
                                    "user_id": st.session_state.user_id
                                }
                            )
                            st.rerun()
                for child in children.get(fid, []):
                    show_folder(child["folder_id"])

        roots = [f for f in folders if f["parent_folder_id"] is None]
        for r in roots:
            show_folder(r["folder_id"])