def get_datasource_identifier_from_path(path: str) -> str:
    """Get the datasource identifier from a path"""
    try:
        # Extract datasource name from path (second component after /data/)
        path_parts = path.split("/")
        data_index = path_parts.index("data")
        if data_index + 2 >= len(path_parts):
            raise ValueError(f"Invalid file path structure: {path}")
        return path_parts[data_index + 2]
    except Exception as e:
        # Do not use logger here
        raise ValueError(f"Invalid file path structure: {path}")
    
def validate_name(name: str) -> str:
    """Validate name format and security, raise if invalid and return the str if ok"""
    try:
        if not name:
            raise ValueError("Name cannot be empty")
        
        if len(name) > 255:
            raise ValueError("Name exceeds maximum length of 255 characters")

        # Check for invalid characters in filename
        invalid_chars = '<>:"|?*\\'
        if any(char in name for char in invalid_chars):
            raise ValueError(
                f"Name contains invalid characters. The following characters are not allowed: {invalid_chars}"
            )
        
        # Check if the path is relative and doesn't start with a /
        if name.startswith('/'):
            raise ValueError("Name must be relative to the user's home directory")
        
        # Split path and validate datasource identifier
        path_parts = name.split('/')
        if len(path_parts) < 1:
            raise ValueError(
                "Invalid path format. Path must include datasource identifier (e.g., 'files/your-file.txt')"
            )
                    
        # Check for path traversal attempts
        if '..' in name or '//' in name:
            raise ValueError(
                "Invalid path: potential path traversal detected"
            )
        
        return name
    except Exception as e:
        raise ValueError(f"Invalid name: {name}")