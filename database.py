import sqlite3
import os
import json

DB_DIR = "data"
DB_FILE = os.path.join(DB_DIR, "projects.db")


def init_db():
    try:
        if not os.path.exists(DB_DIR):
            os.makedirs(DB_DIR)
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        # Create tables
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT NOT NULL,
                assigned_admins TEXT DEFAULT '[]',
                assigned_by TEXT DEFAULT NULL,
                client_email TEXT DEFAULT NULL,
                progress INTEGER DEFAULT 0,
                status TEXT DEFAULT 'pending',
                last_update TEXT DEFAULT NULL
            )
        """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS availability (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                accepting_projects BOOLEAN NOT NULL,
                reopen_date TEXT NOT NULL
            )
        """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS project_updates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                update_text TEXT NOT NULL,
                update_date TEXT NOT NULL,
                updated_by TEXT NOT NULL,
                FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE
            )
        """
        )

        # Create clients table with reset_token column
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS clients (
                email TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                password TEXT NOT NULL,
                reset_token TEXT DEFAULT NULL
            )
        """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS assignment_status (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                admin_username TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE,
                UNIQUE(project_id, admin_username)
            )
        """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                sender TEXT NOT NULL,
                recipient TEXT NOT NULL,
                message TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                read BOOLEAN DEFAULT 0,
                FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE
            )
        """
        )

        # Check if the reset_token column exists in clients table
        cursor.execute("PRAGMA table_info(clients)")
        columns = [column[1] for column in cursor.fetchall()]

        if "reset_token" not in columns:
            # Add the reset_token column to the clients table
            cursor.execute("ALTER TABLE clients ADD COLUMN reset_token TEXT DEFAULT NULL")

        # Insert default availability if not exists
        cursor.execute("SELECT COUNT(*) FROM availability")
        if cursor.fetchone()[0] == 0:
            cursor.execute(
                "INSERT INTO availability (id, accepting_projects, reopen_date) VALUES (1, 1, 'TBA')"
            )

        conn.commit()
    except sqlite3.Error as e:
        print(f"Database error in init_db: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

def add_project(name, description, client_email=None):
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO projects (name, description, client_email) VALUES (?, ?, ?)",
            (name, description, client_email),
        )
        conn.commit()
    except sqlite3.Error as e:
        print(f"Database error in add_project: {e}")
    finally:
        if 'conn' in locals():
            conn.close()


def get_projects(assigned=None):
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        if assigned is None:
            cursor.execute("SELECT * FROM projects")
        elif assigned:
            cursor.execute("SELECT * FROM projects WHERE assigned_admins != '[]'")
        else:
            cursor.execute(
                "SELECT * FROM projects WHERE assigned_admins = '[]' OR assigned_admins IS NULL"
            )

        projects = cursor.fetchall()
        return projects
    except sqlite3.Error as e:
        print(f"Database error in get_projects: {e}")
        return []
    finally:
        if 'conn' in locals():
            conn.close()


def delete_project(project_id):
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM projects WHERE id = ?", (project_id,))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Database error in delete_project: {e}")
    finally:
        if 'conn' in locals():
            conn.close()


def get_availability():
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT accepting_projects, reopen_date FROM availability WHERE id = 1"
        )
        result = cursor.fetchone()
        return {"accepting": bool(result[0]), "reopen_date": result[1]}
    except sqlite3.Error as e:
        print(f"Database error in get_availability: {e}")
        return None
    finally:
        if 'conn' in locals():
            conn.close()


def update_availability(status, reopen_date):
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE availability SET accepting_projects = ?, reopen_date = ? WHERE id = 1",
            (status, reopen_date),
        )
        conn.commit()
    except sqlite3.Error as e:
        print(f"Database error in update_availability: {e}")
    finally:
        if 'conn' in locals():
            conn.close()


def assign_project(project_id, admins, assigned_by):
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        if isinstance(admins, str):
            admins = [admins]

        admins_json = json.dumps(admins)

        if admins:
            cursor.execute(
                "UPDATE projects SET assigned_admins = ?, assigned_by = ? WHERE id = ?",
                (admins_json, assigned_by, project_id),
            )

            # Add entries to assignment_status table for each admin
            for admin in admins:
                cursor.execute(
                    "INSERT OR REPLACE INTO assignment_status (project_id, admin_username, status) VALUES (?, ?, 'pending')",
                    (project_id, admin),
                )
        else:
            cursor.execute(
                "UPDATE projects SET assigned_admins = '[]', assigned_by = NULL WHERE id = ?",
                (project_id,),
            )
            # Clear assignment status entries
            cursor.execute(
                "DELETE FROM assignment_status WHERE project_id = ?", (project_id,)
            )

        conn.commit()
    except sqlite3.Error as e:
        print(f"Database error in assign_project: {e}")
    finally:
        if 'conn' in locals():
            conn.close()


def get_assigned_projects(admin):
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        # Get all projects where the admin has accepted the assignment
        cursor.execute(
            """
            SELECT p.* FROM projects p
            JOIN assignment_status a ON p.id = a.project_id
            WHERE a.admin_username = ? AND a.status = 'accepted'
            """,
            (admin,),
        )

        assigned_projects = cursor.fetchall()
        return assigned_projects
    except sqlite3.Error as e:
        print(f"Database error in get_assigned_projects: {e}")
        return []
    finally:
        if 'conn' in locals():
            conn.close()


def get_pending_assignments(admin):
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT p.* FROM projects p
            JOIN assignment_status a ON p.id = a.project_id
            WHERE a.admin_username = ? AND a.status = 'pending'
            """,
            (admin,),
        )

        pending_assignments = cursor.fetchall()
        return pending_assignments
    except sqlite3.Error as e:
        print(f"Database error in get_pending_assignments: {e}")
        return []
    finally:
        if 'conn' in locals():
            conn.close()


def accept_assignment(project_id, admin):
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        # Update just this admin's status
        cursor.execute(
            "UPDATE assignment_status SET status = 'accepted' WHERE project_id = ? AND admin_username = ?",
            (project_id, admin),
        )

        conn.commit()
    except sqlite3.Error as e:
        print(f"Database error in accept_assignment: {e}")
    finally:
        if 'conn' in locals():
            conn.close()


def reject_assignment(project_id, admin):
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        # Get current assigned admins
        cursor.execute("SELECT assigned_admins FROM projects WHERE id = ?", (project_id,))
        result = cursor.fetchone()

        if result:
            admins = json.loads(result[0])
            if admin in admins:
                admins.remove(admin)

                # Remove this admin from assignment_status
                cursor.execute(
                    "DELETE FROM assignment_status WHERE project_id = ? AND admin_username = ?",
                    (project_id, admin),
                )

                # Update the project's assigned admins list
                cursor.execute(
                    "UPDATE projects SET assigned_admins = ? WHERE id = ?",
                    (json.dumps(admins), project_id),
                )

                conn.commit()

    except sqlite3.Error as e:
        print(f"Database error in reject_assignment: {e}")
    finally:
        if 'conn' in locals():
            conn.close()


def update_project_progress(project_id, progress, status, last_update=None):
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        if last_update:
            cursor.execute(
                "UPDATE projects SET progress = ?, status = ?, last_update = ? WHERE id = ?",
                (progress, status, last_update, project_id),
            )
        else:
            cursor.execute(
                "UPDATE projects SET progress = ?, status = ? WHERE id = ?",
                (progress, status, project_id),
            )

        conn.commit()
    except sqlite3.Error as e:
        print(f"Database error in update_project_progress: {e}")
    finally:
        if 'conn' in locals():
            conn.close()


def add_project_update(project_id, update_text, update_date, updated_by):
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO project_updates (project_id, update_text, update_date, updated_by) VALUES (?, ?, ?, ?)",
            (project_id, update_text, update_date, updated_by),
        )
        conn.commit()
    except sqlite3.Error as e:
        print(f"Database error in add_project_update: {e}")
    finally:
        if 'conn' in locals():
            conn.close()


def get_project_updates(project_id):
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM project_updates WHERE project_id = ? ORDER BY update_date DESC",
            (project_id,),
        )
        updates = cursor.fetchall()
        return updates
    except sqlite3.Error as e:
        print(f"Database error in get_project_updates: {e}")
        return []
    finally:
        if 'conn' in locals():
            conn.close()


def get_project_by_id(project_id):
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
        project = cursor.fetchone()
        return project
    except sqlite3.Error as e:
        print(f"Database error in get_project_by_id: {e}")
        return None
    finally:
        if 'conn' in locals():
            conn.close()


def get_client_projects(client_email):
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM projects WHERE client_email = ?", (client_email,))
        projects = cursor.fetchall()
        return projects
    except sqlite3.Error as e:
        print(f"Database error in get_client_projects: {e}")
        return []
    finally:
        if 'conn' in locals():
            conn.close()


def register_client(email, name, password):
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        # Check if client already exists
        cursor.execute("SELECT COUNT(*) FROM clients WHERE email = ?", (email,))
        if cursor.fetchone()[0] > 0:
            return False

        cursor.execute(
            "INSERT INTO clients (email, name, password) VALUES (?, ?, ?)",
            (email, name, password),
        )
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Database error in register_client: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()


def authenticate_client(email, password):
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM clients WHERE email = ? AND password = ?", (email, password)
        )
        client = cursor.fetchone()
        return client
    except sqlite3.Error as e:
        print(f"Database error in authenticate_client: {e}")
        return None
    finally:
        if 'conn' in locals():
            conn.close()


def get_client_by_email(email):
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM clients WHERE email = ?", (email,))
        client = cursor.fetchone()
        return client
    except sqlite3.Error as e:
        print(f"Database error in get_client_by_email: {e}")
        return None
    finally:
        if 'conn' in locals():
            conn.close()


def send_message(project_id, sender, recipient, message, timestamp):
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO messages (project_id, sender, recipient, message, timestamp) VALUES (?, ?, ?, ?, ?)",
            (project_id, sender, recipient, message, timestamp),
        )
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Database error in send_message: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()


def get_messages(project_id, user):
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT * FROM messages 
            WHERE project_id = ? AND (sender = ? OR recipient = ? OR recipient = 'all')
            ORDER BY timestamp ASC
            """,
            (project_id, user, user),
        )
        messages = cursor.fetchall()
        return messages
    except sqlite3.Error as e:
        print(f"Database error in get_messages: {e}")
        return []
    finally:
        if 'conn' in locals():
            conn.close()


def mark_messages_as_read(project_id, recipient):
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE messages SET read = 1 WHERE project_id = ? AND recipient = ?",
            (project_id, recipient),
        )
        conn.commit()
    except sqlite3.Error as e:
        print(f"Database error in mark_messages_as_read: {e}")
    finally:
        if 'conn' in locals():
            conn.close()


def get_unread_message_count(user):
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM messages WHERE recipient = ? AND read = 0", (user,)
        )
        count = cursor.fetchone()[0]
        return count
    except sqlite3.Error as e:
        print(f"Database error in get_unread_message_count: {e}")
        return 0
    finally:
        if 'conn' in locals():
            conn.close()


def get_project_admins(project_id):
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT admin_username FROM assignment_status 
            WHERE project_id = ? AND status = 'accepted'
            """,
            (project_id,),
        )
        admins = [row[0] for row in cursor.fetchall()]
        return admins
    except sqlite3.Error as e:
        print(f"Database error in get_project_admins: {e}")
        return []
    finally:
        if 'conn' in locals():
            conn.close()


def update_reset_token(email, token):
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("UPDATE clients SET reset_token = ? WHERE email = ?", (token, email))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Database error in update_reset_token: {e}")
    finally:
        if 'conn' in locals():
            conn.close()



def validate_reset_token(email, token):
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT reset_token FROM clients WHERE email = ?", (email,))
        stored_token = cursor.fetchone()
        if stored_token:
            return stored_token[0] == token
        else:
            return False
    except sqlite3.Error as e:
        print(f"Database error in validate_reset_token: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()


def update_client_password(email, new_password):
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("UPDATE clients SET password = ? WHERE email = ?", (new_password, email))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Database error in update_client_password: {e}")
    finally:
        if 'conn' in locals():
            conn.close()
