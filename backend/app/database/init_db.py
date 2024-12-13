from app.database.initialization.database_initializer import get_database_initializer

def initialize_database():
    """Initialize the database using the singleton initializer"""
    initializer = get_database_initializer()
    initializer.initialize()
