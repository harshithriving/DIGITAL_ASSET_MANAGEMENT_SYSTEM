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

    # -------------------- CREATE PROJECT --------------------
    if menu == "➕ Create Project":
        st.subheader("➕ Create New Project")
        project_name = st.text_input("Project Name")
        description = st.text_area("Project Description")

        st.markdown("---")
        st.subheader("📂 Upload Initial Files (Optional)")
        st.caption("Upload files directly to each folder. They will be stored in ImageKit.")

        col1, col2 = st.columns(2)
        with col1:
            videos_files = st.file_uploader("📹 Videos", type=None, accept_multiple_files=True, key="videos_upload")
            images_files = st.file_uploader("🖼️ Images", type=None, accept_multiple_files=True, key="images_upload")
        with col2:
            audio_files = st.file_uploader("🎵 Audio", type=None, accept_multiple_files=True, key="audio_upload")
            others_files = st.file_uploader("📄 Others", type=None, accept_multiple_files=True, key="others_upload")

        # Expandable section for simulated file creation (by name)
        with st.expander("➕ Or add files by name (simulated)"):
            st.caption("Format: `filename.ext, size_in_MB` (one per line). Example: `video.mp4, 5`")
            col1, col2 = st.columns(2)
            with col1:
                videos_input = st.text_area("📹 Videos (simulated)", height=100,
                                           placeholder="video1.mp4, 5\nintro.mov, 10")
                images_input = st.text_area("🖼️ Images (simulated)", height=100,
                                           placeholder="logo.png, 2\nbanner.jpg, 3")
            with col2:
                audio_input = st.text_area("🎵 Audio (simulated)", height=100,
                                           placeholder="sound.mp3, 1\nvoice.wav, 0.5")
                others_input = st.text_area("📄 Others (simulated)", height=100,
                                           placeholder="document.pdf, 2.5\narchive.zip, 5")

        if st.button("Create Project"):
            if not project_name:
                st.error("Project name required")
                return

            # 1. Create the project
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

            # 2. Get folder IDs
            struct_res = requests.get(f"{API_URL}/project/full/{project_id}")
            struct_data = safe_json(struct_res)
            if not struct_data:
                st.warning("Could not retrieve folder structure; files not uploaded.")
                return

            folders = struct_data.get("folders", [])
            folder_map = {f["folder_name"]: f["folder_id"] for f in folders}

            # 3. Upload real files to ImageKit with progress tracking
            uploaded_counts = {}
            folder_file_map = {
                "Videos": videos_files,
                "Images": images_files,
                "Audio": audio_files,
                "Others": others_files
            }

            # Collect all files to upload with their folder names
            upload_tasks = []
            for folder_name, file_list in folder_file_map.items():
                if folder_name in folder_map and file_list:
                    for file in file_list:
                        upload_tasks.append((folder_name, file, folder_map[folder_name]))

            if upload_tasks:
                st.subheader("📤 Uploading Files...")
                progress_bar = st.progress(0)
                status_text = st.empty()
                success_count = 0
                total = len(upload_tasks)

                for idx, (folder_name, file, folder_id) in enumerate(upload_tasks):
                    status_text.text(f"Uploading {file.name} to {folder_name}...")
                    files = {'file': file}
                    data = {
                        'folder_id': folder_id,
                        'uploaded_by': st.session_state.user_id
                    }
                    upload_res = requests.post(f"{API_URL}/upload-to-imagekit", files=files, data=data)
                    if upload_res.status_code == 201:
                        success_count += 1
                        uploaded_counts[folder_name] = uploaded_counts.get(folder_name, 0) + 1
                    else:
                        error_msg = upload_res.json().get('error', 'Unknown error') if upload_res.text else 'Upload failed'
                        st.error(f"Failed to upload {file.name} to {folder_name}: {error_msg}")
                    # Update progress bar
                    progress_bar.progress((idx + 1) / total)

                status_text.text(f"✅ Upload complete. {success_count} of {total} files uploaded successfully.")
                progress_bar.empty()
                st.success(f"Uploaded {success_count} files successfully.")

            # 4. Create simulated files (by name) if provided
            folder_inputs = {
                "Videos": videos_input,
                "Images": images_input,
                "Audio": audio_input,
                "Others": others_input
            }
            created_counts = {}
            error_files = []
            for folder_name, input_text in folder_inputs.items():
                if folder_name not in folder_map:
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
                    try:
                        size_mb = float(size_str)
                        size_bytes = int(size_mb * 1024 * 1024)
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
                    else:
                        error_files.append(f"Failed to create {fname} in {folder_name}")
                if count:
                    created_counts[folder_name] = count

            # 5. Summary
            if uploaded_counts:
                st.success("Real files uploaded successfully to ImageKit:")
                for folder, count in uploaded_counts.items():
                    st.write(f"- {folder}: {count} file(s)")
            if created_counts:
                st.info("Simulated files created successfully:")
                for folder, count in created_counts.items():
                    st.write(f"- {folder}: {count} simulated file(s)")
            if error_files:
                st.error("Errors encountered in simulated files:")
                for err in error_files:
                    st.write(f"- {err}")

            if st.button("View Project Now"):
                st.session_state["selected_project_id"] = project_id
                st.info("Switch to 'My Projects' and select the project to view files.")

    # -------------------- MY PROJECTS --------------------
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
        )
        project_id = selected_project["project_id"]

        st.subheader("📌 Project Info")
        st.write(selected_project["description"])

        # Team info
        st.subheader("👥 Team")
        pm_id = selected_project.get("project_manager_user_id")
        if pm_id:
            pm_res = requests.get(f"{API_URL}/user/{pm_id}")
            if pm_res.status_code == 200:
                pm_data = pm_res.json()
                pm_name = pm_data.get("name", "Unknown")
            else:
                pm_name = "Unknown"
        else:
            pm_name = "Not assigned"
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

        # Files under review
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
        struct_res = requests.get(f"{API_URL}/project/full/{project_id}")
        struct_data = safe_json(struct_res)
        if not struct_data:
            st.warning("No structure found")
            return

        folders = struct_data.get("folders", [])
        files = struct_data.get("files", [])

        if not folders:
            st.warning("No folders found")
            return

        # Validate files list
        if not isinstance(files, list):
            st.error("Invalid files data format from server")
            files = []
        else:
            files = [f for f in files if isinstance(f, dict) and 'file_id' in f and 'folder_id' in f]

        # Add new file upload (real) with progress indicator
        st.markdown("### ➕ Upload New File (Real)")
        folder_map = {f["folder_name"]: f["folder_id"] for f in folders}
        selected_folder = st.selectbox("Select Folder", list(folder_map.keys()))
        uploaded_file = st.file_uploader("Choose a file to upload", type=None)
        if st.button("Upload File to ImageKit"):
            if uploaded_file is not None:
                with st.spinner(f"Uploading {uploaded_file.name} to {selected_folder}..."):
                    files_data = {'file': uploaded_file}
                    form_data = {
                        'folder_id': folder_map[selected_folder],
                        'uploaded_by': st.session_state.user_id
                    }
                    upload_res = requests.post(f"{API_URL}/upload-to-imagekit", files=files_data, data=form_data)
                if upload_res.status_code == 201:
                    st.success(f"✅ {uploaded_file.name} uploaded successfully to ImageKit!")
                    st.rerun()
                else:
                    error_msg = upload_res.json().get('error', 'Unknown error') if upload_res.text else 'Upload failed'
                    st.error(f"Upload failed: {error_msg}")
            else:
                st.warning("Please select a file")
        st.divider()

        # Tree view
        folder_map_full = {f["folder_id"]: f for f in folders}
        children = {}
        for f in folders:
            children.setdefault(f["parent_folder_id"], []).append(f)

        def show_folder(fid):
            folder = folder_map_full.get(fid)
            if not folder:
                return
            with st.expander(f"📁 {folder['folder_name']}"):
                # Files in this folder
                folder_files = [f for f in files if f.get("folder_id") == fid]
                for file in folder_files:
                    with st.expander(f"📄 {file.get('file_name', 'Unknown')}"):
                        # Load comments
                        comments = safe_json(requests.get(f"{API_URL}/file/comments/{file['file_id']}")) or []
                        for c in comments:
                            st.info(f"User {c['user_id']}: {c['comment_text']}")
                        # Add comment
                        comment = st.text_input("Add comment", key=f"c_{file['file_id']}")
                        if st.button("Submit", key=f"s_{file['file_id']}"):
                            if comment:
                                requests.post(
                                    f"{API_URL}/comments",
                                    json={
                                        "comment": comment,
                                        "file_id": file["file_id"],
                                        "user_id": st.session_state.user_id
                                    }
                                )
                                st.rerun()
                # Subfolders
                for child in children.get(fid, []):
                    show_folder(child["folder_id"])

        roots = [f for f in folders if f.get("parent_folder_id") is None]
        for r in roots:
            show_folder(r["folder_id"])