import datetime
import json
import urllib.parse

import streamlit as st

from database import (accept_assignment, add_project, add_project_update,
                      assign_project, authenticate_client, delete_project,
                      get_assigned_projects, get_availability,
                      get_client_by_email, get_client_projects, get_messages,
                      get_pending_assignments, get_project_admins,
                      get_project_by_id, get_project_updates, get_projects,
                      get_unread_message_count, init_db, mark_messages_as_read,
                      register_client, reject_assignment, send_message,
                      update_availability, update_project_progress)

# Load admin credentials from Streamlit secrets
admin_users = st.secrets["general"]["ADMIN_USERS"].split(",")
admin_passwords = st.secrets["general"]["ADMIN_PASSWORDS"].split(",")


# Initialize DB
init_db()

# Load project availability from the database
availability_status = get_availability()
ACCEPTING_PROJECTS = availability_status["accepting"]
REOPEN_DATE = availability_status["reopen_date"]

# Set page config
st.set_page_config(page_title="CraftMyAI - AI Solutions", page_icon="🛠️", layout="wide")

# Center align the app
st.markdown(
    """
    <style>
        .block-container { max-width: 800px; margin: auto; }
    </style>
    """,
    unsafe_allow_html=True,
)

# Sidebar Navigation
st.sidebar.title("CraftMyAI")

# Authentication Variables
if "logged_in_admin" not in st.session_state:
    st.session_state.logged_in_admin = None

if "logged_in_client" not in st.session_state:
    st.session_state.logged_in_client = None

# Determine navigation based on user type
if st.session_state.logged_in_admin:
    page = st.sidebar.radio(
        "",
        [
            "🏠 Home",
            "🔐 Admin Dashboard",
            "📝 Logout",
        ],
    )
elif st.session_state.logged_in_client:
    page = st.sidebar.radio(
        "",
        [
            "🏠 Home",
            "📊 Client Dashboard",
            "📩 Request AI Solution",
            "📝 Feedback",
            "📞 Contact Us",
            "ℹ️ About Us",
            "📝 Logout",
        ],
    )
else:
    page = st.sidebar.radio(
        "",
        [
            "🏠 Home",
            "📩 Request AI Solution",
            "📝 Feedback",
            "📞 Contact Us",
            "ℹ️ About Us",
            "🔐 Admin Panel",
            "👤 Client Login",
        ],
    )

# Logout functionality
if page == "📝 Logout":
    if st.session_state.logged_in_admin:
        st.session_state.logged_in_admin = None
    if st.session_state.logged_in_client:
        st.session_state.logged_in_client = None
    st.rerun()

# Home Page
if page == "🏠 Home":
    st.title("🛠️ Welcome to CraftMyAI")

    st.write("")
    if ACCEPTING_PROJECTS:
        st.success("✅ We are currently accepting new requests!")
    else:
        st.warning(
            f"⚠️ We are **not accepting new requests** right now. Next availability: **{REOPEN_DATE}**."
        )
    st.write("")

    st.subheader("Get your custom AI solutions, tailored to your needs.")
    st.markdown(
        """
        - 🤖 **Personalized AI solutions** for businesses and individuals
        - 🛠️ **1-month free support** after delivery
        - 💰 **Transparent pricing based on complexity**
        - 🚀 **Affordable MVPs to kickstart your idea**
        - 🎨 **Customization at every step**
        
        🔥 **Let's bring your AI vision to life!**
    """
    )
    st.write("")
    st.image(
        "https://images.pexels.com/photos/6153068/pexels-photo-6153068.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=2",
        width=800,
    )

# Request AI Solution Form
elif page == "📩 Request AI Solution":
    st.title("📩 Request Your AI Solution")

    if not ACCEPTING_PROJECTS:
        st.warning(
            f"🚧 We are not accepting new requests until **{REOPEN_DATE}**. You can still submit, and we will respond when available."
        )

    client_email = None
    if st.session_state.logged_in_client:
        client = get_client_by_email(st.session_state.logged_in_client)
        if client:
            st.info(f"Submitting as: {client[1]} ({client[0]})")
            client_email = client[0]

    with st.form("ai_request_form"):
        name = st.text_input("Your Name", value="" if not client_email else client[1])
        email = st.text_input(
            "Your Email", value="" if not client_email else client_email
        )
        project_details = st.text_area("Project Description")
        budget = st.number_input("Estimated Budget (in INR)", min_value=0, step=100)
        submit_button = st.form_submit_button("Submit Request")

    if submit_button:
        if name and email and project_details:
            recipient_email = "help.craftmyai@gmail.com"
            subject = urllib.parse.quote("New AI Solution Request")
            body = urllib.parse.quote(
                f"Name: {name}\nEmail: {email}\nBudget: ₹{budget}\n\nProject Details:\n{project_details}"
            )
            mailto_link = f"mailto:{recipient_email}?subject={subject}&body={body}"
            st.success(
                f"✅ Thank you {name}! Click the button below to send your request via Gmail."
            )
            st.markdown(f"📩 [Send Email]({mailto_link})", unsafe_allow_html=True)
        else:
            st.error("⚠️ Please fill in all required fields before submitting.")

# Feedback Page
elif page == "📝 Feedback":
    st.title("📝 CraftMyAI Feedback Form")
    st.write("We value your feedback! Help us improve by sharing your thoughts.")

    client_name = ""
    client_email = ""
    if st.session_state.logged_in_client:
        client = get_client_by_email(st.session_state.logged_in_client)
        if client:
            client_name = client[1]
            client_email = client[0]
            st.info(f"Submitting as: {client_name} ({client_email})")

    name = st.text_input("Your Name", value=client_name)
    email = st.text_input("Your Email", value=client_email)
    rating = st.slider("Rate your experience (1-5)", 1, 5, 3)
    feedback = st.text_area("Your Feedback")

    if st.button("Submit Feedback"):
        if name and email and feedback:
            recipient_email = "help.craftmyai@gmail.com"
            subject = urllib.parse.quote("CraftMyAI Feedback")
            body = urllib.parse.quote(
                f"Name: {name}\nEmail: {email}\nRating: {rating}/5\n\nFeedback:\n{feedback}"
            )
            mailto_link = f"mailto:{recipient_email}?subject={subject}&body={body}"
            st.success(
                f"✅ Thank you {name}! Click the button below to send your feedback via Gmail."
            )
            st.markdown(f"📝 [Send Feedback]({mailto_link})", unsafe_allow_html=True)
        else:
            st.error("⚠️ Please complete all fields before submitting.")

    st.write("---")

# Contact Us Page
elif page == "📞 Contact Us":
    st.title("📞 Contact Us")
    st.write("Have questions or want to discuss an AI project? Reach out to us!")

    client_name = ""
    client_email = ""
    if st.session_state.logged_in_client:
        client = get_client_by_email(st.session_state.logged_in_client)
        if client:
            client_name = client[1]
            client_email = client[0]
            st.info(f"Submitting as: {client_name} ({client_email})")

    with st.form("contact_form"):
        contact_name = st.text_input("Your Name", value=client_name)
        contact_email = st.text_input("Your Email", value=client_email)
        message = st.text_area("Your Message")
        submit_contact = st.form_submit_button("Send Message")

    if submit_contact:
        if contact_name and contact_email and message:
            recipient_email = "help.craftmyai@gmail.com"
            subject = urllib.parse.quote("Contact Request")
            body = urllib.parse.quote(
                f"Name: {contact_name}\nEmail: {contact_email}\n\nMessage:\n{message}"
            )
            mailto_link = f"mailto:{recipient_email}?subject={subject}&body={body}"
            st.success(
                f"✅ Thank you {contact_name}! Click the button below to send your message via Gmail."
            )
            st.markdown(f"📞 [Send Message]({mailto_link})", unsafe_allow_html=True)
        else:
            st.error("⚠️ Please fill in all fields before submitting.")

# About Us Page
elif page == "ℹ️ About Us":
    st.title("ℹ️ About CraftMyAI")
    st.write(
        "We specialize in developing AI solutions tailored for businesses and individuals."
    )
    st.markdown(
        """
        - 🎯 **Mission:** Deliver high-quality AI solutions with seamless support.
        - 🌍 **Vision:** Making AI accessible to businesses of all sizes.
    """
    )

# Client Login/Registration Page
elif page == "👤 Client Login":
    st.title("👤 Client Portal")

    tab1, tab2 = st.tabs(["Login", "Register"])

    with tab1:
        st.subheader("Login to Your Account")
        email = st.text_input("Email Address", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")

        if st.button("Login"):
            if email and password:
                client = authenticate_client(email, password)
                if client:
                    st.session_state.logged_in_client = email
                    st.success(f"✅ Welcome back, {client[1]}!")
                    st.rerun()
                else:
                    st.error("❌ Invalid credentials. Please try again.")
            else:
                st.error("⚠️ Please enter both email and password.")

    with tab2:
        st.subheader("Create a New Account")
        new_name = st.text_input("Full Name", key="reg_name")
        new_email = st.text_input("Email Address", key="reg_email")
        new_password = st.text_input("Password", type="password", key="reg_password")
        confirm_password = st.text_input(
            "Confirm Password", type="password", key="confirm_password"
        )

        if st.button("Register"):
            if new_name and new_email and new_password:
                if new_password != confirm_password:
                    st.error("❌ Passwords do not match!")
                else:
                    # Check if email already exists
                    client = get_client_by_email(new_email)
                    if client:
                        st.error(
                            "❌ Email already registered. Please use a different email or log in."
                        )
                    else:
                        result = register_client(new_email, new_name, new_password)
                        if result:
                            st.success(
                                "✅ Registration successful! You can now log in."
                            )
                        else:
                            st.error("❌ An error occurred during registration.")
            else:
                st.error("⚠️ Please fill in all fields.")


# Client Dashboard
elif page == "📊 Client Dashboard":
    st.title("📊 Client Dashboard")

    if not st.session_state.logged_in_client:
        st.error("❌ Please log in to access your dashboard.")
        st.stop()

    client = get_client_by_email(st.session_state.logged_in_client)
    st.write("")
    st.write(f"Welcome, **{client[1]}**! Here you can track your project progress.")

    projects = get_client_projects(client[0])

    if not projects:
        st.info(
            "You don't have any projects yet. Head to 'Request AI Solution' to submit a project."
        )
    else:
        st.write("---")
        st.subheader("Your Projects")

        for project in projects:
            project_id = project[0]
            project_name = project[1]
            project_description = project[2]
            assigned_admins = json.loads(project[3] if project[3] else "[]")
            progress = project[6] if project[6] is not None else 0
            status = project[7] if project[7] else "pending"
            last_update = project[8]

            # Get list of admins who have actually accepted the assignment
            active_admins = get_project_admins(project_id)

            with st.expander(f"📋 {project_name} ({status.upper()})"):
                tabs = st.tabs(["Details", "Updates", "Messages"])

                with tabs[0]:
                    st.subheader("Project Details")
                    st.markdown(f"```\n{project_description}\n```")

                    # Progress bar
                    st.write(f"Progress: {progress}% | Last Updated: {last_update}")
                    st.progress(progress / 100.0)

                    if active_admins:
                        st.write(f"**Assigned Team:** {', '.join(active_admins)}")
                    else:
                        st.write("**Status:** Waiting for team assignment")

                with tabs[1]:
                    # Show updates
                    updates = get_project_updates(project_id)
                    if updates:
                        st.subheader("Project Updates")
                        st.write("")
                        for update in updates:
                            update_text = update[2]
                            update_date = update[3]
                            updated_by = update[4]

                            st.markdown(
                                f"""
                            *{update_date}* by **{updated_by}**
                            
                            {update_text}
                            """
                            )
                            st.write("---")
                    else:
                        st.info("No updates have been posted for this project yet.")

                with tabs[2]:
                    # Messaging functionality for client
                    st.subheader("Messages")

                    if not active_admins:
                        st.info(
                            "Messages will be available once admins are assigned to your project."
                        )
                    else:
                        # Mark messages as read when client views them
                        mark_messages_as_read(project_id, client[0])

                        # Show existing messages
                        messages = get_messages(project_id, client[0])

                        if messages:
                            for msg in messages:
                                sender = msg[2]
                                message_text = msg[4]
                                timestamp = msg[5]

                                if sender == client[0]:
                                    st.markdown(
                                        f"""
                                    <div style="padding: 10px; border-radius: 5px; margin-bottom: 10px;">
                                        <strong>You</strong> ({timestamp})<br>
                                        {message_text}
                                    </div>
                                    """,
                                        unsafe_allow_html=True,
                                    )
                                else:
                                    st.markdown(
                                        f"""
                                    <div style="padding: 10px; border-radius: 5px; margin-bottom: 10px;">
                                        <strong>{sender}</strong> ({timestamp})<br>
                                        {message_text}
                                    </div>
                                    """,
                                        unsafe_allow_html=True,
                                    )
                        else:
                            st.info("No messages yet. Start the conversation!")

                        # Send a new message
                        new_message = st.text_area(
                            "New message", key=f"msg_{project_id}"
                        )
                        recipient = st.selectbox(
                            "Send to:",
                            ["All admins"] + active_admins,
                            key=f"recipient_{project_id}",
                        )

                        if st.button("Send Message", key=f"send_msg_{project_id}"):
                            if new_message:
                                current_time = datetime.datetime.now().strftime(
                                    "%Y-%m-%d %H:%M"
                                )

                                # Convert "All admins" to internal representation
                                actual_recipient = (
                                    "all" if recipient == "All admins" else recipient
                                )

                                # Send the message
                                send_message(
                                    project_id,
                                    client[0],
                                    actual_recipient,
                                    new_message,
                                    current_time,
                                )
                                st.success("Message sent!")
                                st.rerun()
                            else:
                                st.error("Please enter a message.")

            st.write("")

# Admin Panel Authentication
elif page == "🔐 Admin Panel" or page == "🔐 Admin Dashboard":

    st.title("🔐 Admin Dashboard")
    st.write("")
    if st.session_state.logged_in_admin is None:
        admin_username = st.text_input("Admin Username:")
        admin_password = st.text_input("Admin Password:", type="password")

        if st.button("Login"):
            if (
                admin_username in admin_users
                and admin_passwords[admin_users.index(admin_username)] == admin_password
            ):
                st.success(f"✅ Welcome, {admin_username}!")
                st.session_state.logged_in_admin = admin_username  # Store in session
                st.rerun()
            else:
                st.error("❌ Incorrect credentials! Access denied.")
                st.stop()
    else:
        st.success(f"✅ Logged in as {st.session_state.logged_in_admin}")

        if st.button("Logout"):
            st.session_state.logged_in_admin = None
            st.rerun()

        logged_in_admin = st.session_state.logged_in_admin

        # Check for unread messages
        unread_count = get_unread_message_count(logged_in_admin)
        if unread_count > 0:
            st.warning(f"You have {unread_count} unread message(s) from clients.")

        # Project Availability Management
        st.write("")
        st.write("")
        st.subheader("Project Availability")
        st.write("")
        accepting_projects = st.checkbox(
            "Accepting New Projects", value=ACCEPTING_PROJECTS
        )
        reopen_date = st.text_input("Reopen Date", REOPEN_DATE)

        if st.button("Update Availability"):
            update_availability(accepting_projects, reopen_date)
            st.success("✅ Availability Updated!")
            st.rerun()
        st.write("")
        st.write("")

        # Pending Project Assignments section
        st.subheader("Pending Project Assignments")
        st.write("")
        pending_assignments = get_pending_assignments(logged_in_admin)

        if not pending_assignments:
            st.info("You have no pending project assignments.")
        else:
            for assignment in pending_assignments:
                st.write("")
                st.write(f"**{assignment[1]}**")
                st.markdown(f"```\n{assignment[2]}\n```")
                assigned_admins = json.loads(assignment[3] if assignment[3] else "[]")
                st.markdown(f"Assigned to: **{', '.join(assigned_admins)}**")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"✅ Accept", key=f"accept_{assignment[0]}"):
                        accept_assignment(assignment[0], logged_in_admin)
                        st.success(f"Project '{assignment[1]}' accepted!")
                        st.rerun()
                with col2:
                    if st.button(f"❌ Reject", key=f"reject_{assignment[0]}"):
                        reject_assignment(assignment[0], logged_in_admin)
                        st.success(f"Project '{assignment[1]}' rejected!")
                        st.rerun()
                st.write("")
        st.write("")
        st.write("")

        # Project Management
        st.subheader("Unassigned Project Requests")
        st.write("")
        project_list = get_projects(assigned=False)
        if not project_list:
            st.info("No unassigned projects.")
        for project in project_list:
            st.write("")
            st.write(f"**{project[1]}**")
            st.markdown(f"```\n{project[2]}\n```")

            # Create multiselect for admin assignment
            selected_admins = st.multiselect(
                f"Assign to admins:", admin_users, key=f"admin_select_{project[0]}"
            )

            if st.button(f"📝 Assign Project", key=f"assign_{project[0]}"):
                if selected_admins:
                    assign_project(project[0], selected_admins, logged_in_admin)
                    admin_list = ", ".join(selected_admins)
                    st.success(f"✅ Project '{project[1]}' assigned to {admin_list}!")
                    st.rerun()
                else:
                    st.warning("Please select at least one admin.")
            st.write("")
        st.write("")
        st.write("")

        # Assigned Projects (For logged in admin)
        st.subheader("Your Assigned Projects")
        st.write("")
        assigned_projects = get_assigned_projects(logged_in_admin)

        if not assigned_projects:
            st.info("You have no assigned projects.")
        else:
            for project in assigned_projects:
                project_id = project[0]
                project_name = project[1]
                project_description = project[2]
                assigned_admins = json.loads(project[3] if project[3] else "[]")
                client_email = project[5]
                progress = project[6] if project[6] is not None else 0
                status = project[7] if project[7] else "in progress"
                last_update = project[8]

                with st.expander(f"📋 {project_name}"):
                    # Create tabs for better organization
                    tabs = st.tabs(["Project Details", "Updates", "Messages"])

                    with tabs[0]:
                        st.markdown(f"```\n{project_description}\n```")

                        if client_email:
                            client = get_client_by_email(client_email)
                            if client:
                                st.markdown(f"**Client:** {client[1]} ({client_email})")
                            else:
                                st.markdown(f"**Client Email:** {client_email}")

                        # Get active admins (who have accepted the assignment)
                        active_admins = get_project_admins(project_id)
                        st.markdown(f"**Team:** {', '.join(active_admins)}")

                        # Progress tracking
                        col1, col2 = st.columns(2)
                        with col1:
                            new_progress = st.slider(
                                "Progress (%)",
                                0,
                                100,
                                int(progress),
                                key=f"progress_{project_id}",
                            )
                        with col2:
                            status_options = [
                                "pending",
                                "in progress",
                                "review",
                                "completed",
                                "on hold",
                            ]
                            new_status = st.selectbox(
                                "Status",
                                status_options,
                                (
                                    status_options.index(status)
                                    if status in status_options
                                    else 0
                                ),
                                key=f"status_{project_id}",
                            )

                        if st.button("Save Changes", key=f"save_status_{project_id}"):
                            current_date = datetime.datetime.now().strftime(
                                "%Y-%m-%d %H:%M"
                            )
                            update_project_progress(
                                project_id, new_progress, new_status, current_date
                            )
                            st.success("✅ Project status updated successfully!")
                            st.rerun()

                    with tabs[1]:
                        update_text = st.text_area(
                            "Add Update", key=f"update_{project_id}"
                        )

                        if st.button("Post Update", key=f"post_update_{project_id}"):
                            if update_text:
                                current_date = datetime.datetime.now().strftime(
                                    "%Y-%m-%d %H:%M"
                                )
                                add_project_update(
                                    project_id,
                                    update_text,
                                    current_date,
                                    logged_in_admin,
                                )
                                st.success("✅ Update posted successfully!")
                                st.rerun()
                            else:
                                st.warning("Please enter an update message.")

                        # Show updates
                        updates = get_project_updates(project_id)
                        if updates:
                            st.subheader("Project Updates")
                            for update in updates:
                                update_text = update[2]
                                update_date = update[3]
                                updated_by = update[4]

                                st.markdown(
                                    f"""
                                ---
                                *{update_date}* by **{updated_by}**
                                
                                {update_text}
                                """
                                )

                    with tabs[2]:
                        # Messaging system for admin
                        st.subheader("Client Communication")

                        if not client_email:
                            st.info("No client associated with this project.")
                        else:
                            # First mark any messages to this admin as read
                            mark_messages_as_read(project_id, logged_in_admin)

                            # Display existing messages
                            messages = get_messages(project_id, logged_in_admin)

                            if messages:
                                for msg in messages:
                                    sender = msg[2]
                                    message_text = msg[4]
                                    timestamp = msg[5]

                                    # Format differently based on sender
                                    if sender == logged_in_admin:
                                        st.markdown(
                                            f"""
                                        <div style="padding: 10px; border-radius: 5px; margin-bottom: 10px;">
                                            <strong>You</strong> ({timestamp})<br>
                                            {message_text}
                                        </div>
                                        """,
                                            unsafe_allow_html=True,
                                        )
                                    elif sender == client_email:
                                        client_name = client[1] if client else sender
                                        st.markdown(
                                            f"""
                                        <div style="padding: 10px; border-radius: 5px; margin-bottom: 10px;">
                                            <strong>{client_name}</strong> ({timestamp})<br>
                                            {message_text}
                                        </div>
                                        """,
                                            unsafe_allow_html=True,
                                        )
                                    else:
                                        st.markdown(
                                            f"""
                                        <div style="padding: 10px; border-radius: 5px; margin-bottom: 10px;">
                                            <strong>{sender}</strong> ({timestamp})<br>
                                            {message_text}
                                        </div>
                                        """,
                                            unsafe_allow_html=True,
                                        )
                            else:
                                st.info("No messages yet. Start the conversation!")

                            # Send a new message
                            new_message = st.text_area(
                                "New message", key=f"admin_msg_{project_id}"
                            )

                            if st.button(
                                "Send Message", key=f"admin_send_msg_{project_id}"
                            ):
                                if new_message:
                                    current_time = datetime.datetime.now().strftime(
                                        "%Y-%m-%d %H:%M"
                                    )

                                    # Send the message to the client
                                    send_message(
                                        project_id,
                                        logged_in_admin,
                                        client_email,
                                        new_message,
                                        current_time,
                                    )
                                    st.success("Message sent!")
                                    st.rerun()
                                else:
                                    st.error("Please enter a message.")

                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"❌ Delete Project", key=f"delete_{project_id}"):
                        delete_project(project_id)
                        st.success(f"Project '{project_name}' deleted!")
                        st.rerun()

                st.write("")
        st.write("")
        st.write("")

        # Add New Project
        st.subheader("Add a New Project")
        st.write("")
        new_project_name = st.text_input("Project Name")
        new_project_description = st.text_area("Project Details")
        client_email = st.text_input("Client Email")

        if (
            st.button("Add Project")
            and new_project_name
            and new_project_description
            and client_email
        ):
            add_project(
                new_project_name,
                new_project_description,
                client_email if client_email else None,
            )
            st.success(f"✅ Project '{new_project_name}' added!")
            st.rerun()

        st.write("")
        st.write("")
