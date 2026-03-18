import streamlit as st

def file_grid():
    cols = st.columns(5)

    for i in range(10):
        with cols[i % 5]:
            st.image(
                "https://picsum.photos/200",
                use_container_width=True
            )
            st.caption(f"image_{i}.jpg")