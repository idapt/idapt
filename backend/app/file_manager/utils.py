from base64 import urlsafe_b64decode
from fastapi import HTTPException
from typing import Tuple
import base64

import logging
logger = logging.getLogger("uvicorn")

def decode_path_safe(encoded_original_path: str) -> str:
    try:
        if not encoded_original_path:
            return ""
        return urlsafe_b64decode(encoded_original_path.encode()).decode()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid path encoding")


def validate_path(original_path: str) -> str:
    """Validate path format and security, raise if invalid and return the str if ok"""
    try:
        if not original_path:
            raise HTTPException(status_code=400, detail="File path cannot be empty")
        
        if len(original_path) > 255:
            raise HTTPException(status_code=400, detail="File name exceeds maximum length of 255 characters")

        # Check for invalid characters in filename
        invalid_chars = '<>:"|?*\\'
        if any(char in original_path for char in invalid_chars):
            raise HTTPException(
                status_code=400,
                detail=f"File path contains invalid characters. The following characters are not allowed: {invalid_chars}"
            )
        
        # Check if the path is relative and doesn't start with a /
        if original_path.startswith('/'):
            raise HTTPException(status_code=400, detail="Path must be relative to the user's home directory")
        
        # Split path and validate datasource identifier
        path_parts = original_path.split('/')
        if len(path_parts) < 1:
            raise HTTPException(
                status_code=400, 
                detail="Invalid path format. Path must include datasource identifier (e.g., 'files/your-file.txt')"
            )
                    
        # Check for path traversal attempts
        if '..' in original_path or '//' in original_path:
            raise HTTPException(
                status_code=400,
                detail="Invalid path: potential path traversal detected"
            )
        
        return original_path
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Path validation error: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid path format: {str(e)}"
        )
    
def preprocess_base64_file(base64_content: str) -> Tuple[bytes, str | None]:
    """ Decode base64 file content and return the file data and extension """
    try:
        # Validate base64 content format
        if ',' not in base64_content:
            raise ValueError(
                "Invalid base64 format. Expected format: 'data:<mediatype>;base64,<data>'"
            )
            
        header, data = base64_content.split(",", 1)
        
        # Validate header format
        if not header.startswith('data:') or ';base64' not in header:
            raise ValueError(
                "Invalid base64 header format. Expected format: 'data:<mediatype>;base64'"
            )
            
        try:
            mime_type = header.split(";")[0].split(":", 1)[1]
        except IndexError:
            raise ValueError("Could not extract mime type from base64 header")

        # Decode base64 data
        try:
            decoded_data = base64.b64decode(data)
        except Exception:
            raise ValueError("Invalid base64 data encoding")

        return decoded_data, mime_type

    except ValueError as e:
        logger.error(f"Error preprocessing base64 file: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error preprocessing base64 file: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while processing file upload"
        )