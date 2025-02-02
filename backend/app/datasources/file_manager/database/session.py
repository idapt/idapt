
from app.database.utils.service import get_session
from app.api.user_path import get_user_data_dir
from app.datasources.file_manager.service.service import initialize_file_manager_db
from app.api.utils import get_user_id
from app.datasources.database.models import Datasource, DatasourceType
from app.datasources.database.session import get_datasources_db_session

from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException
from pathlib import Path
import logging

logger = logging.getLogger("uvicorn")

# Get a session for the file manager database
def get_datasources_file_manager_db_session(
    datasource_name: str,
    user_id: str = Depends(get_user_id),
    datasources_db_session: Session = Depends(get_datasources_db_session)
):
    """
    Get a session for the file manager database
    """
    try:
        datasource = datasources_db_session.query(Datasource).filter(Datasource.name == datasource_name).first()
        if not datasource:
            raise HTTPException(status_code=400, detail="Datasource not found")
        if datasource.type != DatasourceType.FILES.name:
            raise HTTPException(status_code=400, detail="Datasource is not of type files")
        db_path = Path(get_user_data_dir(user_id), datasource.identifier, "file_manager.db")
        # Create the parent directories if they don't exist
        db_path.parent.mkdir(parents=True, exist_ok=True)
        script_location = Path(__file__).parent
        from app.datasources.file_manager.database.models import Base
        models_declarative_base_class = Base
        with get_session(str(db_path), str(script_location), models_declarative_base_class) as session:
            # Always initialize default data if needed before yielding the session
            initialize_file_manager_db(session, user_id, datasource_name)
            yield session
    except Exception as e:
        logger.error(f"Error in get_datasources_file_manager_db_session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    
def get_datasources_file_manager_session(
        user_id: str, 
        datasource_name: str, 
        datasources_db_session: Session
    ) -> Session:
    try:
        datasource = datasources_db_session.query(Datasource).filter(Datasource.name == datasource_name).first()
        if not datasource:
            raise HTTPException(status_code=400, detail="Datasource not found")
        if datasource.type != DatasourceType.FILES.name:
            raise HTTPException(status_code=400, detail="Datasource is not of type files")
        db_path = Path(get_user_data_dir(user_id), datasource.identifier, "file_manager.db")
        # Create the parent directories if they don't exist
        db_path.parent.mkdir(parents=True, exist_ok=True)
        script_location = Path(__file__).parent
        from app.datasources.file_manager.database.models import Base
        models_declarative_base_class = Base
        with get_session(str(db_path), str(script_location), models_declarative_base_class) as session:
            # Always initialize default data if needed before yielding the session
            initialize_file_manager_db(session, user_id, datasource_name)
            return session
    except Exception as e:
        logger.error(f"Error in get_datasources_file_manager_session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))