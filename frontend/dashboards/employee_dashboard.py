import streamlit as st

def show_employee_dashboard():


    col1, col2 = st.columns([8, 1])

    with col2:
        st.markdown("###")
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.role = None
            st.rerun()

    st.title("🧑‍💻 Employee Dashboard")

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