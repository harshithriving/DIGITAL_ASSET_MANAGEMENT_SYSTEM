import streamlit as st

# ==============================
# STORAGE CALCULATION
# ==============================
def calculate_storage():
    TOTAL_LIMIT_MB = 500

    total_bytes = 0

    if "projects" in st.session_state:
        for project in st.session_state.projects.values():

            for category in project["RAW Files"].values():
                for f in category:
                    total_bytes += f.size

            for f in project["Edited Files"]:
                total_bytes += f.size

    used_mb = total_bytes / (1024 * 1024)
    left_mb = TOTAL_LIMIT_MB - used_mb

    return round(used_mb, 2), round(left_mb, 2), TOTAL_LIMIT_MB


# ==============================
# EMPLOYEE DASHBOARD
# ==============================
def show_employee_dashboard():

    # 🔥 LOGOUT
    col1, col2 = st.columns([8, 1])
    with col2:
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.role = None
            st.rerun()

    st.title("🧑‍💻 Employee Dashboard")

    # ==============================
    # 💾 STORAGE
    # ==============================
    used, left, total = calculate_storage()

    col1, col2 = st.columns(2)
    col1.metric("💾 Storage Used", f"{used} MB")
    col2.metric("📦 Storage Left", f"{left} MB / {total} MB")

    percent = used / total if total != 0 else 0
    st.progress(percent)

    st.divider()

    # ==============================
    # TABS
    # ==============================
    tab1, tab2 = st.tabs(["📂 Current Project", "📤 Upload Edited Files"])

    # ==============================
    # TAB 1 — PROJECT VIEW
    # ==============================
    with tab1:

        # ✅ FIXED PROJECT STRUCTURE
        projects = {
            "Marketing Video Campaign": {
                "description": "Social media ad campaign editing",
                "assigned_by": "Ashwini Bhagat",

                "files": [
                    ("intro_raw.mp4", "Video"),
                    ("background_music.wav", "Audio"),
                    ("product_images.zip", "Images"),
                    ("brand_guidelines.pdf", "Document")
                ],

                "Edited Files": [
                    "intro_video.mp4"
                ],

                "Comments": [
                    {
                        "file": "intro_video.mp4",
                        "comment": "Reduce brightness",
                        "by": "Client"
                    },
                    {
                        "file": "intro_video.mp4",
                        "comment": "Add transition",
                        "by": "Project Manager"
                    }
                ]
            },

            "Website UI Design": {
                "description": "Landing page UI editing",
                "assigned_by": "Priya Patel",

                "files": [
                    ("homepage.psd", "Design"),
                    ("icons.zip", "Assets"),
                    ("fonts.zip", "Fonts")
                ],

                "Edited Files": [
                    "homepage_v2.psd"
                ],

                "Comments": [
                    {
                        "file": "homepage_v2.psd",
                        "comment": "Improve color palette",
                        "by": "Client"
                    }
                ]
            }
        }

        # SELECT PROJECT
        selected_project = st.selectbox("Select Project", list(projects.keys()))
        project = projects[selected_project]

        with st.expander("📂 View Project Details", expanded=True):

            st.write(f"**📌 Project:** {selected_project}")
            st.write(f"**📝 Description:** {project['description']}")
            st.write(f"**👨‍💼 Assigned By:** {project['assigned_by']}")

            st.divider()

            # ==============================
            # RAW FILES
            # ==============================
            st.subheader("📥 RAW Files")

            for file, ftype in project["files"]:
                col1, col2 = st.columns([4,1])
                col1.write(f"📄 {file} — {ftype}")

                col2.download_button(
                    "⬇ Download",
                    data=b"Sample",
                    file_name=file,
                    key=f"{selected_project}_{file}"
                )

            st.divider()

            # ==============================
            # EDITED FILES + COMMENTS
            # ==============================
            st.subheader("📤 Edited Files & Feedback")

            for file in project["Edited Files"]:

                st.markdown(f"### 📄 {file}")

                # COMMENTS FILTER
                file_comments = [
                    c for c in project["Comments"] if c["file"] == file
                ]

                if not file_comments:
                    st.info("No comments yet")
                else:
                    for c in file_comments:
                        st.info(f"{c['by']}: {c['comment']}")

                st.markdown("---")

    # ==============================
    # TAB 2 — UPLOAD
    # ==============================
    with tab2:
        st.subheader("📤 Upload Edited Files")

        uploaded_files = st.file_uploader(
            "Upload Files",
            accept_multiple_files=True
        )

        if uploaded_files:
            for file in uploaded_files:
                st.success(f"Uploaded: {file.name}")

        if st.button("🚀 Submit"):
            st.success("Submitted for review!")