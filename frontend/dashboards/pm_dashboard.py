import streamlit as st

# -------- Session State --------
if "pm_projects" not in st.session_state:
    st.session_state.pm_projects = {
        "Marketing Campaign": {
            "employees": [],
            "final_files": []
        },
        "Website Redesign": {
            "employees": [],
            "final_files": []
        }
    }

if "employees" not in st.session_state:
    st.session_state.employees = [
        {"name": "Aakarshan", "available": True},
        {"name": "Rohit", "available": True},
        {"name": "Neha", "available": False},
        {"name": "Aman", "available": True}
    ]


# -------- Dashboard --------
def show_pm_dashboard():

    col1, col2 = st.columns([8, 1])

    with col2:
        st.markdown("###")
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.role = None
            st.rerun() 
    

    st.title("🧑‍💼 Project Manager Dashboard")

    menu = st.sidebar.radio(
        "Menu",
        ["📁 Assigned Projects", "👥 Assign Employees", "📝 Final Reviews"]
    )

    # ---------------- ASSIGNED PROJECTS ----------------
    if menu == "📁 Assigned Projects":
        st.subheader("Projects Assigned To You")

        for project in st.session_state.pm_projects:
            st.markdown(f"### 📌 {project}")

    # ---------------- ASSIGN EMPLOYEES ----------------
    elif menu == "👥 Assign Employees":
        st.subheader("Assign Employees to Project")

        projects = list(st.session_state.pm_projects.keys())
        selected_project = st.selectbox("Select Project", projects)

        st.write("### Available Employees")

        available_employees = [
            emp for emp in st.session_state.employees if emp["available"]
        ]

        selected_emp = st.multiselect(
            "Select Employees",
            [emp["name"] for emp in available_employees]
        )

        if st.button("Assign"):
            st.session_state.pm_projects[selected_project]["employees"].extend(selected_emp)

            # mark them busy
            for emp in st.session_state.employees:
                if emp["name"] in selected_emp:
                    emp["available"] = False

            st.success("Employees Assigned Successfully")

        st.divider()

        st.write("### Assigned Employees")
        assigned = st.session_state.pm_projects[selected_project]["employees"]
        if assigned:
            for emp in assigned:
                st.write(f"• {emp}")
        else:
            st.info("No employees assigned yet")

    # ---------------- FINAL REVIEWS ----------------
    elif menu == "📝 Final Reviews":
        st.subheader("Review Final Files")

        projects = list(st.session_state.pm_projects.keys())
        selected_project = st.selectbox("Select Project", projects)

        files = st.session_state.pm_projects[selected_project]["final_files"]

        if not files:
            st.info("No final files uploaded yet")
        else:
            for file in files:
                st.write(f"📄 {file.name}")

                comment = st.text_input(
                    f"Comment on {file.name}",
                    key=f"pm_comment_{file.name}"
                )

                if st.button(f"Submit Review for {file.name}"):
                    st.success("Review Submitted")