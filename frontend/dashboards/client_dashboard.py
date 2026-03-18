import streamlit as st
from datetime import datetime

# -------- Session State --------
if "projects" not in st.session_state:
    st.session_state.projects = {}

if "selected_project" not in st.session_state:
    st.session_state.selected_project = None


# -------- Helper --------
def create_project(project_name, description, files):
    st.session_state.projects[project_name] = {
        "description": description,
        "created_at": datetime.now().strftime("%d %b %Y"),
        "RAW Files": {
            "Images": [],
            "Videos": [],
            "Audio": [],
            "Others": []
        },
        "Edited Files": ["test_vid.mp4"],  # Dummy file for testing
        "Comments": []
    }

    if files:
        st.session_state.projects[project_name]["RAW Files"]["Others"].extend(files)


# -------- Storage Helper --------
def calculate_storage():
    TOTAL_LIMIT_MB = 500

    total_bytes = 0

    for project in st.session_state.projects.values():

        # RAW files
        for category in project["RAW Files"].values():
            for f in category:
                total_bytes += f.size

        # Edited files (handle both string & file)
        for f in project["Edited Files"]:
            if hasattr(f, "size"):
                total_bytes += f.size

    used_mb = total_bytes / (1024 * 1024)
    left_mb = TOTAL_LIMIT_MB - used_mb

    return round(used_mb, 2), round(left_mb, 2), TOTAL_LIMIT_MB


# -------- Dashboard --------
def show_client_dashboard():

    # 🔥 Logout
    col1, col2 = st.columns([8, 1])
    with col2:
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.role = None
            st.rerun()

    # -------- Storage --------
    used, left, total = calculate_storage()

    col1, col2 = st.columns(2)
    col1.metric("💾 Storage Used", f"{used} MB")
    col2.metric("📦 Storage Left", f"{left} MB / {total} MB")

    st.divider()

    st.title("👤 Client Dashboard")

    menu = st.sidebar.radio(
        "Menu",
        ["📁 My Projects", "➕ Create Project"]
    )

    # ================= CREATE PROJECT =================
    if menu == "➕ Create Project":

        st.subheader("➕ Create New Project")

        with st.form("create_project_form"):

            project_name = st.text_input("Project Name")
            description = st.text_area("Project Description")

            initial_files = st.file_uploader(
                "Upload Initial RAW Files (Optional)",
                accept_multiple_files=True
            )

            submitted = st.form_submit_button("Create Project")

            if submitted:
                if not project_name:
                    st.error("Project name is required")
                else:
                    create_project(project_name, description, initial_files)
                    st.success("✅ Project Created Successfully")

    # ================= MY PROJECTS =================
    elif menu == "📁 My Projects":

        st.subheader("📁 Your Projects")

        if not st.session_state.projects:
            st.info("No projects yet. Create one.")
            return

        project_list = list(st.session_state.projects.keys())
        selected = st.selectbox("Select Project", project_list)

        project = st.session_state.projects[selected]

        st.divider()

        # -------- Project Info --------
        st.subheader("📌 Project Info")
        st.write(f"**Name:** {selected}")
        st.write(f"**Description:** {project['description']}")
        st.write(f"**Created On:** {project['created_at']}")

        st.divider()

        # -------- RAW FILES --------
        st.subheader("📂 RAW Files")

        raw = project["RAW Files"]

        for category in raw:
            st.markdown(f"### 📁 {category}")

            uploaded_files = st.file_uploader(
                f"Upload to {category}",
                accept_multiple_files=True,
                key=f"{selected}_{category}"
            )

            if uploaded_files:
                raw[category].extend(uploaded_files)
                st.success(f"Uploaded to {category}")

            if raw[category]:
                for f in raw[category]:
                    st.write(f"• {f.name}")

        st.divider()

        # -------- EDITED FILES + COMMENTS --------
        st.subheader("📝 Edited Files (For Review)")

        edited_files = project["Edited Files"]

        if not edited_files:
            st.info("No edited files received yet.")
        else:
            for file in edited_files:

                # Handle string OR uploaded file
                file_name = file if isinstance(file, str) else file.name

                st.write(f"📄 {file_name}")

                # COMMENT INPUT
                comment = st.text_input(
                    f"Comment on {file_name}",
                    key=f"comment_{selected}_{file_name}"
                )

                # SUBMIT BUTTON
                if st.button(
                    "Submit Comment",
                    key=f"btn_{selected}_{file_name}"
                ):

                    if comment:
                        project["Comments"].append({
                            "file": file_name,
                            "comment": comment,
                            "by": "Client",
                            "time": datetime.now().strftime("%H:%M")
                        })
                        st.success("Comment submitted")
                    else:
                        st.warning("Enter comment first")

                # SHOW COMMENTS
                file_comments = [
                    c for c in project["Comments"] if c["file"] == file_name
                ]

                if file_comments:
                    st.markdown("### 💬 Comments")
                    for c in file_comments:
                        st.info(f"{c['by']} ({c['time']}): {c['comment']}")

                st.markdown("---")