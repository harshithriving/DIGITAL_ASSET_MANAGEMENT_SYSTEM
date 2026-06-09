import streamlit as st
import requests
import time

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

    menu = st.sidebar.radio("Menu", ["📁 Assigned Projects", "👥 Assign Employees", "📝 Final Reviews", "🧪 Transaction Simulator"])

    # Get projects for the PM
    res = requests.get(f"{API_URL}/pm/projects/{pm_id}")
    if res.status_code != 200:
        st.error("Failed to load projects")
        return
    projects = res.json()
    if not projects:
        st.info("No projects assigned")
        # Still allow simulator? We need at least one project. If none, show warning.
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
        if not projects:
            st.warning("No projects available to assign employees.")
        else:
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
                failed = []
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
                            failed.append(f"{emp['name']}: {error_msg}")
                        else:
                            st.success(f"✅ {emp['name']} assigned successfully.")
                if failed:
                    for err in failed:
                        st.error(f"❌ {err}")
                else:
                    st.success("All selected employees assigned successfully.")

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
        if not projects:
            st.warning("No projects available.")
        else:
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
                            commenter = c.get('name', f"User {c.get('user_id', 'Unknown')}")
                            st.info(f"{commenter}: {c['comment_text']}")
                    st.markdown("---")

    elif menu == "🧪 Transaction Simulator":
        st.subheader("Transaction Simulator: Concurrent Assignment")
        st.markdown("""
        This demonstrates how the database transaction prevents assigning an employee to more than **2 projects** and avoids duplicate assignments.
        The simulator sends **two assignment requests** sequentially (simulating two PMs trying to assign the same employee at the same time).
        The second request will fail if it would violate the limit or duplicate rule.
        """)

        if not projects:
            st.warning("No projects available. Please ensure you have at least one project assigned.")
        else:
            # Fetch employees
            emp_res = requests.get(f"{API_URL}/employees")
            if emp_res.status_code != 200:
                st.error("Failed to load employees")
                return
            employees = emp_res.json()
            if not employees:
                st.info("No employees found.")
            else:
                # Employee selection
                emp_names = [e["name"] for e in employees]
                selected_emp_name = st.selectbox("Select Employee", emp_names, key="sim_emp")
                employee = next(e for e in employees if e["name"] == selected_emp_name)
                employee_id = employee["user_id"]

                # Two project selections
                project_names = list(project_map.keys())
                col1, col2 = st.columns(2)
                with col1:
                    proj1_name = st.selectbox("First Project", project_names, key="proj1")
                    proj1_id = project_map[proj1_name]["project_id"]
                with col2:
                    proj2_name = st.selectbox("Second Project", project_names, key="proj2")
                    proj2_id = project_map[proj2_name]["project_id"]

                # Option to use same project for duplicate test
                same_project = st.checkbox("Use same project for both assignments (test duplicate assignment)")
                if same_project:
                    proj2_id = proj1_id
                    proj2_name = proj1_name

                if st.button("Run Simulation"):
                    # Reset any previous messages
                    st.session_state.sim_messages = []
                    
                    # First assignment
                    with st.spinner("Attempting first assignment..."):
                        res1 = requests.post(f"{API_URL}/pm/assign_employee", json={
                            "project_id": proj1_id,
                            "user_id": employee_id,
                            "granted_by": pm_id
                        })
                        time.sleep(0.5)  # slight delay to simulate concurrency
                    
                    # Second assignment
                    with st.spinner("Attempting second assignment..."):
                        res2 = requests.post(f"{API_URL}/pm/assign_employee", json={
                            "project_id": proj2_id,
                            "user_id": employee_id,
                            "granted_by": pm_id
                        })
                    
                    # Display results
                    st.subheader("Simulation Results")
                    if res1.status_code == 200:
                        st.success(f"✅ First assignment to '{proj1_name}' succeeded.")
                    else:
                        error1 = res1.json().get("error", "Unknown error")
                        st.error(f"❌ First assignment failed: {error1}")
                    
                    if res2.status_code == 200:
                        st.success(f"✅ Second assignment to '{proj2_name}' succeeded.")
                    else:
                        error2 = res2.json().get("error", "Unknown error")
                        st.error(f"❌ Second assignment failed: {error2}")
                    
                    st.info("The transaction ensures that if the second assignment would exceed the limit or duplicate, it is rolled back.")
                    
                    # Optional: Show current assignments for this employee
                    st.subheader("Current Assignments for this Employee")
                    # Get projects assigned to this employee via permissions
                    proj_res = requests.get(f"{API_URL}/employee/projects/{employee_id}")
                    if proj_res.status_code == 200:
                        assigned_projs = proj_res.json()
                        if assigned_projs:
                            for p in assigned_projs:
                                st.write(f"- {p['project_name']} (ID: {p['project_id']})")
                        else:
                            st.write("No projects assigned yet.")
                    else:
                        st.error("Could not fetch employee's projects.")