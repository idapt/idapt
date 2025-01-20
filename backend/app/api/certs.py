import os
import time
from typing import Tuple
import logging

logger = logging.getLogger("uvicorn")

def setup_backend_certs(host_domain: str, deployment_type: str) -> Tuple[str, str]:
    """Setup the backend certs"""
    try:
        ssl_keyfile_path = "/certs/live/" + host_domain + "/privkey.pem"
        ssl_certfile_path = "/certs/live/" + host_domain + "/fullchain.pem"

        if deployment_type == "hosted":
            ssl_keyfile_path = "/etc/certs/tls.key"
            ssl_certfile_path = "/etc/certs/tls.crt"
            # Print the content of the certs folder
            logger.info(f"Certs folder content: {os.listdir('/etc/certs')}")
            # Wait until the certs are ready at /certs
            while not os.path.exists(ssl_keyfile_path) or not os.path.exists(ssl_certfile_path):
                logger.info("Waiting for certs to be ready")
                time.sleep(1)
            
        else:
            # Check if the certs are present in /certs and create them if not
            if not os.path.exists(ssl_keyfile_path) or not os.path.exists(ssl_certfile_path):
                # Create the backend managed tag file to indicate that the certs are managed by the backend
                with open("/certs/backend-managed", "w") as f:
                    f.write("true")
                # Create the certs
                logger.info("Creating certs")
                os.makedirs("/certs/live/" + host_domain, exist_ok=True)
                os.system("openssl req -x509 -newkey rsa:4096 -keyout /certs/live/" + host_domain + "/privkey.pem -out /certs/live/" + host_domain + "/fullchain.pem -days 365 -nodes -subj '/CN=" + host_domain + "'")

            # If they exist and are backend managed, check if the certs are valid
            if os.path.exists("/certs/backend-managed") and os.path.exists("/certs/live/" + os.getenv("HOST_DOMAIN") + "/privkey.pem") and os.path.exists("/certs/live/" + os.getenv("HOST_DOMAIN") + "/fullchain.pem"):
                # If the certs are not valid, regenerate new ones
                if os.system("openssl x509 -in /certs/live/" + host_domain + "/fullchain.pem -noout -text") != 0:
                    logger.info("Certs are not valid, regenerating")
                    os.system("openssl req -x509 -newkey rsa:4096 -keyout /certs/live/" + host_domain + "/privkey.pem -out /certs/live/" + host_domain + "/fullchain.pem -days 365 -nodes -subj '/CN=" + host_domain + "'")

        return ssl_keyfile_path, ssl_certfile_path
    except Exception as e:
        logger.error(f"Error setting up backend certs: {e}")
        raise e