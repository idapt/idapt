#This file is used only in a dev environment to run migrations via the alembic CLI
from logging.config import fileConfig
from alembic import context
from app.database.connection import get_connection_string
from app.database.models import Base

# Configure alembic.ini settings
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set connection string
connection_string = get_connection_string()
config.set_main_option('sqlalchemy.url', connection_string)

# Set target metadata
target_metadata = Base.metadata

# Ignore tables managed by llama index
TABLES_TO_INCLUDE = ["files", "folders", "datasources"]

# Ignore the data_embeddings table
def include_object(object, name, type_, reflected, compare_to):
    """
    Should you include this table or not?
    """
    if type_ == "table" and name in TABLES_TO_INCLUDE:
        return True
    return False

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        include_object=include_object, 
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    from sqlalchemy import engine_from_config
    from sqlalchemy import pool

    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_object=include_object, 
            version_table="alembic_version",
            compare_type=True,
            compare_server_default=True
        )

        with context.begin_transaction():
            context.run_migrations()

# Only run migrations when called via alembic CLI
if context.is_offline_mode() and __name__ == "alembic.env":
    run_migrations_offline()
elif __name__ == "alembic.env":
    run_migrations_online()
