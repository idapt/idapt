import os
import secrets
import string
import psycopg2
from psycopg2 import sql

def generate_random_password(length=32):
    # Exclude problematic characters like quotes, backslashes, etc.
    characters = string.ascii_letters + string.digits + "!@#$%^&*()-_=+[]{}|;:,.<>?/"
    password = ''.join(secrets.choice(characters) for i in range(length))
    return password

def change_superuser_password():
    password_file_path = os.getenv("POSTGRES_PASSWORD_PATH")

    # Check if the password file exists and contains a valid password
    if os.path.exists(password_file_path):
        with open(password_file_path, "r") as f:
            existing_password = f.read().strip()
        if existing_password:
            print("Superuser password already set. Skipping password change.")
            return

    db_password = generate_random_password()
    admin_user = os.getenv("POSTGRES_USER", "postgres")
    admin_password = os.getenv("POSTGRES_PASSWORD", "defaultpassword")
    db_host = os.getenv("POSTGRES_HOST", "localhost")
    db_port = os.getenv("POSTGRES_PORT", "5432")

    # Connect to the PostgreSQL server
    conn = psycopg2.connect(
        dbname="postgres",
        user=admin_user,
        password=admin_password,
        host=db_host,
        port=db_port
    )
    conn.autocommit = True
    cursor = conn.cursor()

    # Store the password securely
    with open(password_file_path, "w") as f:
        f.write(db_password)

    # Change the superuser password
    cursor.execute(sql.SQL("ALTER USER {} WITH PASSWORD %s").format(sql.Identifier(admin_user)), [db_password])

    cursor.close()
    conn.close()