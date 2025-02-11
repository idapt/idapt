import os
import asyncio
from typing import Tuple
import logging
import datetime
import threading

logger = logging.getLogger("uvicorn")

def create_self_signed_cert(host_domain: str, ssl_keyfile_path: str, ssl_certfile_path: str) -> None:
    """Create a self signed cert"""
    try:
        # Create the certs
        logger.info("Creating certs")
        os.makedirs(os.path.dirname(ssl_keyfile_path), exist_ok=True)
        os.makedirs(os.path.dirname(ssl_certfile_path), exist_ok=True)
        # TODO Use cryptography instead of system openssl to reduce dependencies
        os.system("openssl req -x509 -newkey rsa:4096 -keyout " + ssl_keyfile_path + " -out " + ssl_certfile_path + " -days 90 -nodes -subj '/CN=" + host_domain + "'")
        
    except Exception as e:
        logger.error(f"Error creating self signed cert: {e}")
        raise e

def create_and_start_regenerate_task_for_backend_certs(host_domain: str) -> Tuple[str, str]:
    """Create and start a task that will check and regenerate the backend certs"""
    try:
        ssl_keyfile_path = "/certs/live/" + host_domain + "/privkey.pem"
        ssl_certfile_path = "/certs/live/" + host_domain + "/fullchain.pem"
            
        # Ensure certificate directory exists
        os.makedirs(os.path.dirname(ssl_keyfile_path), exist_ok=True)
        
        # Check if the certs are present in /certs and create them if not
        if not os.path.exists(ssl_keyfile_path) or not os.path.exists(ssl_certfile_path):
            create_self_signed_cert(host_domain, ssl_keyfile_path, ssl_certfile_path)

        # Get the expiration date of the certs
        # TODO Use cryptography instead of system openssl to reduce dependencies
        if check_end_date_of_x509_cert(ssl_certfile_path, 30):
            create_self_signed_cert(host_domain, ssl_keyfile_path, ssl_certfile_path)
        else:
            logger.info("Certs are still valid")
            # Create a daemon thread to run the async task
            def run_async_in_thread(logger: logging.Logger):
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(check_regenerate_certs_task_loop(logger, host_domain, ssl_keyfile_path, ssl_certfile_path))
                except Exception as e:
                    logger.error(f"Certificate regeneration task failed: {e}")
                finally:
                    loop.close()

            # Start the thread with minimal resources
            regeneration_thread = threading.Thread(
                target=run_async_in_thread,
                daemon=True,  # Will terminate when main thread exits
                name="cert-regeneration",
                args=(logger,)
            )
            regeneration_thread.start()
            

        
        return ssl_keyfile_path, ssl_certfile_path
    except Exception as e:
        logger.error(f"Error setting up backend certs: {e}")
        raise e
    
#def get_x509_cert_expiration_date(ssl_certfile_path: str) -> datetime.datetime:
#    """Get the expiration date of the certs"""
#    # TODO Use cryptography instead of system openssl to reduce dependencies
#    expiration_date_in_unix_time = os.system("openssl x509 -in " + ssl_certfile_path + " -noout -enddate")
#    expiration_date = datetime.datetime.fromtimestamp(expiration_date_in_unix_time)
#    logger.info(f"Certs expiration date in unix time: {expiration_date_in_unix_time}")
#    logger.info(f"Certs expiration date: {expiration_date}")
#    return expiration_date

def check_end_date_of_x509_cert(ssl_certfile_path: str, max_days_of_validity_before_regeneration: int = 30) -> bool:
    """Check if the certs are expired or expire in less than max_days_of_validity_before_regeneration days"""
    if os.system("openssl x509 -checkend " + str(max_days_of_validity_before_regeneration * 86400) + " -noout -in " + ssl_certfile_path) == "Certificate will not expire":
        return True
    else:
        return False
    
async def check_regenerate_certs_task_loop(logger: logging.Logger, host_domain: str, ssl_keyfile_path: str, ssl_certfile_path: str, max_days_of_validity_before_regeneration: int = 30, check_interval: int = 5) -> None:
    """
    Check if the certs are expired or expire in less than max_days_of_validity_before_regeneration days and regenerate them
    Check every check_interval days
    """
    try:
        logger.info(f"Starting check and regenerate certs task for {host_domain}")
        while True:
            # Get the expiration date of the certs
            # TODO Use cryptography instead of system openssl to reduce dependencies
            # If the certs are expired or expire in less than 30 days, create new ones
            if check_end_date_of_x509_cert(ssl_certfile_path, max_days_of_validity_before_regeneration):
                logger.info(f"Certs are expired or expire in less than {max_days_of_validity_before_regeneration} days, regenerating them")
                # Delete the old certs
                os.remove(ssl_keyfile_path)
                os.remove(ssl_certfile_path)
                # Regenerate the certs
                create_self_signed_cert(host_domain, ssl_keyfile_path, ssl_certfile_path)
            
            # Wait 15 days before checking again
            # Likely the pod wil restart in the meantime so just in case
            logger.info(f"Waiting {check_interval} days before checking and regenerating certs again")
            await asyncio.sleep(check_interval * 24 * 60 * 60)
    except Exception as e:
        # Wait the check_interval before restarting the task
        await asyncio.sleep(check_interval * 24 * 60 * 60)
        # Restart a task to check the certs again in check_interval days
        asyncio.create_task(check_regenerate_certs_task_loop(host_domain, ssl_keyfile_path, ssl_certfile_path, max_days_of_validity_before_regeneration, check_interval))
        logger.error(f"Error in check and regenerate certs task, restarting it in {check_interval} days: {e}")
        raise e
    
# TODO Implement this to not rely on system openssl anymore
#def generate_self_signed_cert(host_domain: str, days_of_validity: int = 365):
#    import datetime
#    from cryptography import x509
#    from cryptography.hazmat.backends import default_backend
#    from cryptography.hazmat.primitives import hashes
#    from cryptography.hazmat.primitives.asymmetric import rsa
#    from cryptography.hazmat.primitives import serialization
#    from cryptography.x509.oid import NameOID
#
#    one_day = datetime.timedelta(1, 0, 0)
#    private_key = rsa.generate_private_key(
#            public_exponent=65537,
#            key_size=2048,
#            backend=default_backend())
#    public_key = private_key.public_key()
#
#    builder = x509.CertificateBuilder()
#    builder = builder.subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, host_domain)]))
#    builder = builder.issuer_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, host_domain)]))
#    builder = builder.not_valid_before(datetime.datetime.today() - one_day)
#    builder = builder.not_valid_after(datetime.datetime.today() + (one_day*days_of_validity))
#    builder = builder.serial_number(x509.random_serial_number())
#    builder = builder.public_key(public_key)
#    builder = builder.add_extension(
#        x509.SubjectAlternativeName([
#            x509.DNSName(host_domain),
#            x509.DNSName('*.%s' % host_domain),
#        ]),
#        critical=False)
#    builder = builder.add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
#
#    certificate = builder.sign(
#        private_key=private_key, algorithm=hashes.SHA256(),
#        backend=default_backend())
#
#    return (certificate.public_bytes(serialization.Encoding.PEM),
#        private_key.private_bytes(serialization.Encoding.PEM,
#            serialization.PrivateFormat.PKCS8,
#            serialization.NoEncryption()))
#