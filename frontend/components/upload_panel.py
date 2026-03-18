import streamlit as st

def upload_panel():
    st.subheader("Upload Files")

    uploaded_files = st.file_uploader(
        "Drag & Drop Files",
        accept_multiple_files=True
    )

    if uploaded_files:
        st.write(f"**{len(uploaded_files)} Files Selected**")

        cols = st.columns(2)
        for i, file in enumerate(uploaded_files):
            with cols[i % 2]:
                st.image(file, use_container_width=True)
                st.caption(file.name)

        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            st.button("Cancel")
        with col2:
            st.button("Upload Files", type="primary")