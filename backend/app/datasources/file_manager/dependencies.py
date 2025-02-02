from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
import logging

from app.datasources.database.models import Datasource, DatasourceType
from app.datasources.utils import validate_name
from app.datasources.database.session import get_datasources_db_session

logger = logging.getLogger("uvicorn")

async def validate_datasource_is_of_type_files(
    datasource_name: str,
    datasources_db_session: Session = Depends(get_datasources_db_session),
):
    """Dependency to validate if a datasource exists"""
    try:
      try:
        validate_name(datasource_name)
      except ValueError as e:
        raise HTTPException(
          status_code=400,
          detail="Invalid datasource name"
        )

      datasource = datasources_db_session.query(Datasource).filter(
          Datasource.name == datasource_name
      ).first()
      
      if not datasource:
          raise HTTPException(
              status_code=400,
              detail=f"Invalid datasource identifier '{datasource_name}'. Create a datasource first or use a valid datasource identifier"
          )
      if datasource.type != DatasourceType.FILES.name:
        raise HTTPException(
          status_code=400,
          detail="Datasource is not of type files"
        )
      
      return datasource.identifier
    except Exception as e:
        logger.error(f"Error validating datasource: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to validate datasource: {str(e)}")
