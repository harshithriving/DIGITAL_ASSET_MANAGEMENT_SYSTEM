import streamlit as st

def show_projects():
    st.subheader("📁 Projects")

    projects = [
        "Marketing Campaign",
        "Website Redesign",
        "Product Launch",
        "Training Videos"
    ]

    for p in projects:
        st.markdown(f"• {p}")