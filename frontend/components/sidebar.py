import streamlit as st

def sidebar():
    with st.sidebar:
        st.title("Media Library")

        st.selectbox("Filter", ["All", "Images", "Videos", "Documents"])
        st.text_input("🔍 Search")

        st.divider()
        st.subheader("Saved Search")
        st.write("• Sam 30 mb")
        st.write("• Purple")
        st.write("• Name is Sam & jpeg")

        st.divider()
        st.subheader("Storage")
        st.progress(0.2)
        st.caption("3.2 GB of 15 GB used")

        st.button("Upgrade Plan")