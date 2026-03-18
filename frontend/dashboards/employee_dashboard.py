import streamlit as st

# ==============================
# STORAGE CALCULATION
# ==============================
def calculate_storage():
    TOTAL_LIMIT_MB = 500  # Employee limit

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
# EMPLOYEE DASHBOARD
# ==============================
def show_employee_dashboard():

    # 🔥 LOGOUT
    col1, col2 = st.columns([8, 1])
    with col2:
        st.markdown("###")
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.role = None
            st.rerun()

    st.title("🧑‍💻 Employee Dashboard")

    # ==============================
    # 💾 STORAGE OVERVIEW
    # ==============================
    used, left, total = calculate_storage()

    col1, col2 = st.columns(2)

    with col1:
        st.metric("💾 Storage Used", f"{used} MB")

    with col2:
        st.metric("📦 Storage Left", f"{left} MB / {total} MB")

    # Progress bar
    percent = used / total if total != 0 else 0
    st.progress(percent)

    # Status
    if percent < 0.5:
        st.success("🟢 Storage healthy")
    elif percent < 0.8:
        st.warning("🟡 Moderate usage")
    else:
        st.error("🔴 Storage nearly full")

    st.divider()

    # ==============================
    # TABS
    # ==============================
    tab1, tab2 = st.tabs(["📂 Current Project", "📤 Upload Edited Files"])

    # -----------------------------
    # TAB 1 — CURRENT PROJECT
    # -----------------------------
    with tab1:
        st.subheader("📌 Assigned Project")

        st.info("""
        **Project Name:** Marketing Video Campaign  
        **Description:** Social media ad campaign editing  
        **Assigned By:** Project Manager – Ashwini Bhagat
        """)

        st.markdown("---")
        st.subheader("📥 RAW Files to Work On")

        files = [
            ("intro_raw.mp4", "Video"),
            ("background_music.wav", "Audio"),
            ("product_images.zip", "Images"),
            ("brand_guidelines.pdf", "Document")
        ]

        for file, ftype in files:
            col1, col2 = st.columns([4,1])
            col1.write(f"📄 {file} — {ftype}")
            col2.download_button(
                "⬇ Download",
                data=b"Sample file data",
                file_name=file
            )

    # -----------------------------
    # TAB 2 — UPLOAD EDITED FILES
    # -----------------------------
    with tab2:
        st.subheader("📤 Upload Edited Files for Review")

        uploaded_files = st.file_uploader(
            "Upload Edited Files",
            accept_multiple_files=True
        )

        if uploaded_files:
            for file in uploaded_files:
                st.success(f"Uploaded: {file.name}")

        if st.button("🚀 Submit for Review"):
            st.success("Files submitted successfully!")