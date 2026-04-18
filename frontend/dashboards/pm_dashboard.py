import streamlit as st
import requests

API_URL = "http://127.0.0.1:5000"

def show_pm_dashboard():
    col1, col2 = st.columns([8, 1])
    with col2:
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.role = None
            st.session_state.user_id = None
            st.rerun()

    st.title("🧑‍💼 Project Manager Dashboard")

    pm_id = st.session_state.user_id
    if not pm_id:
        st.error("User ID not found")
        return

    menu = st.sidebar.radio("Menu", ["📁 Assigned Projects", "👥 Assign Employees", "📝 Final Reviews"])

    # Get projects
    res = requests.get(f"{API_URL}/pm/projects/{pm_id}")
    if res.status_code != 200:
        st.error("Failed to load projects")
        return
    projects = res.json()
    if not projects:
        st.info("No projects assigned")
        return
    project_map = {p["project_name"]: p for p in projects}

    if menu == "📁 Assigned Projects":
        st.subheader("Projects Assigned To You")
        for p in projects:
            st.markdown(f"### 📌 {p['project_name']}")
            st.write(f"**Description:** {p['description']}")
            st.write(f"**Client:** {p.get('client_name', 'Unknown')}")
            st.write(f"**Created:** {p.get('created_at', '')[:10] if p.get('created_at') else 'N/A'}")
            st.divider()

    elif menu == "👥 Assign Employees":
        st.subheader("Assign Employees")
        selected_name = st.selectbox("Select Project", list(project_map.keys()))
        project = project_map[selected_name]

        # Fetch employees
        emp_res = requests.get(f"{API_URL}/employees")
        if emp_res.status_code != 200:
            st.error("Failed to load employees")
            return
        employees = emp_res.json()
        emp_names = [e["name"] for e in employees]
        selected_emp = st.multiselect("Select Employees", emp_names)

        if st.button("Assign"):
            for emp in employees:
                if emp["name"] in selected_emp:
                    data = {
                        "project_id": project["project_id"],
                        "user_id": emp["user_id"],
                        "granted_by": pm_id
                    }
                    assign_res = requests.post(f"{API_URL}/pm/assign_employee", json=data)
                    if assign_res.status_code != 200:
                        error_msg = assign_res.json().get("error", "Unknown error")
                        st.error(f"Failed to assign {emp['name']}: {error_msg}")
                    else:
                        st.success(f"Assigned {emp['name']} successfully")
            st.rerun()

        st.divider()
        st.subheader("Assigned Employees")
        assign_res = requests.get(f"{API_URL}/project/employees/{project['project_id']}")
        if assign_res.status_code == 200:
            assigned = assign_res.json()
            if assigned:
                for emp in assigned:
                    st.write(f"• {emp['name']}")
            else:
                st.info("No employees assigned yet")
        else:
            st.error("Failed to load assigned employees")

    elif menu == "📝 Final Reviews":
        st.subheader("Review Files")
        selected_name = st.selectbox("Select Project", list(project_map.keys()))
        project = project_map[selected_name]

        file_res = requests.get(f"{API_URL}/file/review/{project['project_id']}")
        if file_res.status_code != 200:
            st.error("Failed to load files")
            return
        files = file_res.json()
        if not files:
            st.info("No files under review")
        else:
            for f in files:
                st.write(f"📄 {f['file_name']} (v{f['version_number']})")
                file_id = f.get('file_id')
                if not file_id:
                    st.error("Missing file_id")
                    continue
                comment = st.text_input(f"Review for {f['file_name']}", key=f"pm_{f['version_id']}")
                if st.button("Submit Review", key=f"btn_{f['version_id']}"):
                    if comment:
                        data = {
                            "comment": comment,
                            "file_id": file_id,
                            "user_id": pm_id
                        }
                        com_res = requests.post(f"{API_URL}/pm/comment", json=data)
                        if com_res.status_code == 200:
                            st.success("Review submitted")
                        else:
                            st.error("Failed to submit review")
                # Show existing comments
                com_res = requests.get(f"{API_URL}/file/comments/{file_id}")
                if com_res.status_code == 200:
                    comments = com_res.json()
                    for c in comments:
                        st.info(f"User {c['user_id']}: {c['comment_text']}")
                st.markdown("---")