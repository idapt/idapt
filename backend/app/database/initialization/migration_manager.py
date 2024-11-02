import logging
from sqlalchemy import create_engine, inspect
from alembic.config import Config
from alembic import command
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
import time

logger = logging.getLogger(__name__)

class DatabaseMigrationManager:
    def __init__(self, connection_string, max_retries=5, retry_delay=2):
        self.connection_string = connection_string
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
    def run_migrations(self):
        for attempt in range(self.max_retries):
            try:
                engine = create_engine(self.connection_string)
                if not self._tables_exist(engine):
                    self._initialize_new_database(engine)
                else:
                    self._run_pending_migrations(engine)
                return True
            except Exception as e:
                if attempt < self.max_retries - 1:
                    logger.warning(f"Migration attempt {attempt + 1} failed: {str(e)}")
                    time.sleep(self.retry_delay)
                else:
                    logger.error("Failed to run migrations after multiple attempts", exc_info=True)
                    return False
                    
    def _tables_exist(self, engine):
        inspector = inspect(engine)
        return bool(inspector.get_table_names())
        
    def _initialize_new_database(self, engine):
        from app.database.models import Base
        Base.metadata.create_all(engine)
        alembic_cfg = Config("alembic.ini")
        command.stamp(alembic_cfg, "head")
        
    def _run_pending_migrations(self, engine):
        alembic_cfg = Config("alembic.ini")
        context = MigrationContext.configure(engine.connect())
        current_rev = context.get_current_revision()
        script = ScriptDirectory.from_config(alembic_cfg)
        head_rev = script.get_current_head()
        
        if current_rev != head_rev:
            command.upgrade(alembic_cfg, "head")
