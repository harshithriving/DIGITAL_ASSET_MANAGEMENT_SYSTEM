import streamlit as st

def file_uploader():
    st.subheader("📤 Upload File")
    uploaded_file = st.file_uploader("Choose a file")

    if uploaded_file:
        st.success(f"{uploaded_file.name} uploaded successfully!")