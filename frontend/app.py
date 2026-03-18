import streamlit as st

st.set_page_config(page_title="DAM System", layout="wide")

# ---------- SESSION STATE ----------
if "role" not in st.session_state:
    st.session_state.role = None

if "name" not in st.session_state:
    st.session_state.name = ""


# ---------- LOGIN PAGE ----------
def login_page():
    st.markdown(
        """
        <h1 style='text-align:center;'>📁 Digital Asset Management System</h1>
        <p style='text-align:center;color:gray;'>Login to Continue</p>
        """,
        unsafe_allow_html=True
    )

    st.divider()

    col1, col2, col3 = st.columns([1,2,1])

    with col2:
        st.subheader("Login")

        role = st.selectbox(
            "Select Role",
            ["Admin", "Project Manager", "Employee", "Client"]
        )

        name = st.text_input("Full Name")
        email = st.text_input("Email")

        if st.button("Login", use_container_width=True):
            if name and email:
                st.session_state.role = role
                st.session_state.name = name
                st.rerun()
            else:
                st.error("Please enter name and email")


# ---------- DASHBOARD ROUTER ----------
def load_dashboard(role):
    st.sidebar.success(f"Logged in as {st.session_state.name}")
    st.sidebar.write(f"Role: **{role}**")

    if role == "Admin":
        from dashboards.admin_dashboard import show_admin_dashboard
        show_admin_dashboard()

    elif role == "Client":
        from dashboards.client_dashboard import show_client_dashboard
        show_client_dashboard()

    elif role == "Employee":
        from dashboards.employee_dashboard import show_employee_dashboard
        show_employee_dashboard()

    elif role == "Project Manager":
        from dashboards.pm_dashboard import show_pm_dashboard
        show_pm_dashboard()


# ---------- MAIN ----------
if st.session_state.role is None:
    login_page()
else:
    load_dashboard(st.session_state.role)