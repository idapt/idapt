import os
import secrets
import string
import psycopg2
from psycopg2 import sql
import logging
from urllib.parse import quote_plus

logger = logging.getLogger(__name__)

class DatabasePasswordManager:
    def __init__(self, password_dir="/backend/secrets"):
        self.password_dir = password_dir
        self.password_file_path = os.path.join(password_dir, "superuser_password.txt")
        
    def generate_password(self, length=32):
        characters = string.ascii_letters + string.digits
        return ''.join(secrets.choice(characters) for _ in range(length))
        
    def get_connection_params(self):
        return {
            "dbname": "postgres",
            "user": os.getenv("POSTGRES_USER", "postgres"),
            "password": os.getenv("POSTGRES_PASSWORD", "defaultpassword"),
            "host": os.getenv("POSTGRES_HOST", "localhost"),
            "port": os.getenv("POSTGRES_PORT", "5432")
        }
        
    def ensure_password_file(self):
        os.makedirs(self.password_dir, exist_ok=True)
        
    def read_stored_password(self):
        if not os.path.exists(self.password_file_path):
            return None
        with open(self.password_file_path, "r") as f:
            return f.read().strip()
            
    def write_password(self, password):
        with open(self.password_file_path, "w") as f:
            f.write(password)
            
    def update_database_password(self, new_password):
        params = self.get_connection_params()
        with psycopg2.connect(**params) as conn:
            conn.autocommit = True
            with conn.cursor() as cursor:
                cursor.execute(
                    sql.SQL("ALTER USER {} WITH PASSWORD %s").format(
                        sql.Identifier(params["user"])
                    ),
                    [new_password]
                )
