import streamlit as st
import requests

st.set_page_config(page_title="DAM System", layout="wide")

API_URL = "http://127.0.0.1:5000"

# ---------- SESSION STATE ----------
if "role" not in st.session_state:
    st.session_state.role = None

if "name" not in st.session_state:
    st.session_state.name = ""

if "user_id" not in st.session_state:
    st.session_state.user_id = None


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

        # 🔥 Role mapping (Frontend → DB)
        role_map = {
            "Admin": "Admin",
            "Project Manager": "ProjectManager",
            "Employee": "Employee",
            "Client": "Client"
        }

        selected_role_label = st.selectbox(
            "Select Role",
            list(role_map.keys())
        )

        role = role_map[selected_role_label]

        # 🔥 FETCH USERS FROM BACKEND
        users = []
        try:
            response = requests.get(f"{API_URL}/users/{role}")

            if response.status_code == 200:
                users = response.json()
            else:
                st.error(f"Backend error: {response.status_code}")

        except Exception as e:
            st.error("Backend not running or API error")
            st.write(e)

        # 🔥 HANDLE EMPTY USERS
        if not users:
            st.warning("No users found for this role")
            return

        # USER DROPDOWN
        user_map = {u["name"]: u["user_id"] for u in users}

        selected_user = st.selectbox(
            "Select User",
            list(user_map.keys())
        )

        # LOGIN BUTTON
        if st.button("Login", use_container_width=True):

            st.session_state.role = selected_role_label
            st.session_state.name = selected_user
            st.session_state.user_id = user_map[selected_user]

            st.rerun()


# ---------- DASHBOARD ROUTER ----------
def load_dashboard(role):
    st.sidebar.success(f"Logged in as {st.session_state.name}")
    st.sidebar.write(f"Role: **{role}**")

    # 🔥 SAFETY CHECK
    if st.session_state.user_id is None:
        st.error("User not set. Please login again.")
        return

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