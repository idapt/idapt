from sqlalchemy.orm import Session
from fastapi import HTTPException
from typing import List, Dict, Any
from app.database.models import Data, DataFile, File

class DBDataManagerService:
    @staticmethod
    def create_data(session: Session, file_ids: List[int], data_content: Dict[str, Any]) -> Data:
        """Create a new data entry and link it to files"""
        try:
            # Create new data entry
            data = Data(data=data_content)
            session.add(data)
            session.flush()  # Flush to get the data.id
            
            # Create file links
            for file_id in file_ids:
                # Verify file exists
                file = session.query(File).filter(File.id == file_id).first()
                if not file:
                    session.rollback()
                    raise HTTPException(status_code=404, detail=f"File with id {file_id} not found")
                
                # Create link
                data_file = DataFile(data_id=data.id, file_id=file_id)
                session.add(data_file)
            
            session.commit()
            return data
            
        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=500, detail=f"Error creating data: {str(e)}")

    @staticmethod
    def modify_data(session: Session, data_id: int, new_data_content: Dict[str, Any]) -> Data:
        """Modify existing data content"""
        try:
            data = session.query(Data).filter(Data.id == data_id).first()
            if not data:
                raise HTTPException(status_code=404, detail=f"Data with id {data_id} not found")
            
            data.data = new_data_content
            session.commit()
            return data
            
        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=500, detail=f"Error modifying data: {str(e)}")

    @staticmethod
    def link_data(session: Session, file_ids: List[int], data_id: int) -> List[DataFile]:
        """Link existing data to additional files"""
        try:
            # Verify data exists
            data = session.query(Data).filter(Data.id == data_id).first()
            if not data:
                raise HTTPException(status_code=404, detail=f"Data with id {data_id} not found")
            
            created_links = []
            for file_id in file_ids:
                # Verify file exists
                file = session.query(File).filter(File.id == file_id).first()
                if not file:
                    session.rollback()
                    raise HTTPException(status_code=404, detail=f"File with id {file_id} not found")
                
                # Check if link already exists
                existing_link = session.query(DataFile).filter(
                    DataFile.data_id == data_id,
                    DataFile.file_id == file_id
                ).first()
                
                if not existing_link:
                    # Create new link
                    data_file = DataFile(data_id=data_id, file_id=file_id)
                    session.add(data_file)
                    created_links.append(data_file)
            
            session.commit()
            return created_links
            
        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=500, detail=f"Error linking data: {str(e)}")

    @staticmethod
    def delete_data(session: Session, data_id: int) -> bool:
        """Delete data and all its file links"""
        try:
            data = session.query(Data).filter(Data.id == data_id).first()
            if not data:
                raise HTTPException(status_code=404, detail=f"Data with id {data_id} not found")
            
            # Delete will cascade to data_files due to relationship configuration
            session.delete(data)
            session.commit()
            return True
            
        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=500, detail=f"Error deleting data: {str(e)}")

    @staticmethod
    def get_data(session: Session, data_id: int) -> Data:
        """Get data by ID"""
        data = session.query(Data).filter(Data.id == data_id).first()
        if not data:
            raise HTTPException(status_code=404, detail=f"Data with id {data_id} not found")
        return data

    @staticmethod
    def get_data_for_file(session: Session, file_id: int) -> List[Data]:
        """Get all data entries linked to a specific file"""
        file = session.query(File).filter(File.id == file_id).first()
        if not file:
            raise HTTPException(status_code=404, detail=f"File with id {file_id} not found")
            
        return session.query(Data).join(DataFile).filter(DataFile.file_id == file_id).all() 