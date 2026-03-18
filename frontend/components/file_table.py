import streamlit as st
import pandas as pd

def show_files():
    st.subheader("📄 Files")

    data = {
        "File Name": ["intro.mp4", "design.psd", "script.docx"],
        "Type": ["Video", "Design", "Document"],
        "Status": ["Approved", "In-Process", "Raw"]
    }

    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True)