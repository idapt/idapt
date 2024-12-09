from typing import Optional
import requests
import logging
import re
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class NginxProxy:
    """Class to manage nginx proxy configurations"""
    
    NGINX_BASE_URL = "http://idapt-nginx:3030"
    #ALLOWED_PORTS = [11434, 443, 8080]  # Add other allowed ports
    
    @classmethod
    def set_custom_ollama_llm_host(cls, host: str) -> None:
        """Set the custom Ollama host in nginx proxy for subsequent requests"""
        try:

            # Validate the host
            parsed = urlparse(host)
            if not parsed.scheme or not parsed.netloc:
                raise ValueError("Invalid host URL format")

            # Reconstruct the base URL and add the trailing slash for more consistent behavior
            #host = f"{parsed.scheme}://{parsed.netloc}"
            
            # If the host url is localhost, replace it with the docker host network ip exposed to the nginx container
            if parsed.hostname == "localhost":
                host = host.replace("localhost", "host.docker.internal")
                
            # Validate hostname format
            if not re.match(r'^[a-zA-Z0-9.-]+$', parsed.hostname):
                raise ValueError("Invalid hostname format")
            
            # Send the host to the nginx proxy
            response = requests.post(
                f"{cls.NGINX_BASE_URL}/set-ollama-host",
                data=host, # Sent with trailing slash
                headers={'Content-Type': 'text/plain'}
            )
            response.raise_for_status()
            logger.info(f"Successfully set custom Ollama host to: {host}")
            #print(f"Successfully set custom Ollama host to: {host}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to set custom Ollama host: {str(e)}")
            raise