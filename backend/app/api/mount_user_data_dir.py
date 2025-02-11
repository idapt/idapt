import os
from contextlib import contextmanager
from datetime import datetime, timedelta
from kubernetes import client, config
from kubernetes.client.rest import ApiException
from filelock import FileLock
import asyncio
import threading

import logging
logger = logging.getLogger("uvicorn")

DATA_FOLDER_PATH = "/data"
USER_DATA_FOLDER_PATH = "/data/{user_uuid}"
USER_DATA_DIR_LOCK_PATH = USER_DATA_FOLDER_PATH + ".lock"
USER_DATA_DIR_LAST_USE_TIMESTAMP_PATH = USER_DATA_FOLDER_PATH + ".timestamp"

MOUNTED_USER_DATA_DIR_CACHE_TIME_SECONDS = 15
PERIODIC_CHECK_MOUNTED_USER_DATA_DIR_SECONDS = 10

def setup_mounted_user_data_dir_cleanup_loop():
    """Setup and start the cleanup loop in a background thread"""
    def run_async_in_thread(logger: logging.Logger):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(cleanup_mounted_user_data_dir_loop(logger))
        except Exception as e:
            logger.error(f"User data cleanup loop failed: {e}")
        finally:
            loop.close()

    logger.info("Setting up unmounted user data directory cleanup loop")
    cleanup_thread = threading.Thread(
        target=run_async_in_thread,
        daemon=True,  # Terminate when main thread exits
        name="user-data-cleanup",
        args=(logger,)
    )
    cleanup_thread.start()


async def cleanup_mounted_user_data_dir_loop(logger: logging.Logger):
    """
    Cleanup mounted user data directories
    """
    try:
        while True:
            # If the deployment type is self-hosted, we do not need to cleanup the mounted user data directories
            if os.environ.get("DEPLOYMENT_TYPE", "self-hosted") == "self-hosted":
                return

            # Wait the PERIODIC_CHECK_UNMOUNTED_USER_DATA_DIR_SECONDS
            await asyncio.sleep(PERIODIC_CHECK_MOUNTED_USER_DATA_DIR_SECONDS)

            # Get all the user data directories filtering for only the directories
            user_data_dirs = [d for d in os.listdir(DATA_FOLDER_PATH) if os.path.isdir(os.path.join(DATA_FOLDER_PATH, d))]
            # For each mounted user data directory
            for user_data_dir in user_data_dirs:
                logger.debug(f"Checking user data directory {user_data_dir}")
                try:
                    # Extract the user_uuid from the user data directory name
                    user_uuid = user_data_dir.split("-")[-1]
                    # Take the lock on the user data directory
                    user_data_dir_lock = FileLock(USER_DATA_DIR_LOCK_PATH.format(user_uuid=user_uuid), timeout=MOUNTED_USER_DATA_DIR_CACHE_TIME_SECONDS) # Wait at most MOUNTED_USER_DATA_DIR_CACHE_TIME_SECONDS for the lock to be released otherwise 
                    with user_data_dir_lock:
                        # Get the last use timestamp
                        last_use_file_content = None
                        try:
                            with open(USER_DATA_DIR_LAST_USE_TIMESTAMP_PATH.format(user_uuid=user_uuid), "r") as f:
                                last_use_file_content = f.read()
                        except Exception as e:
                            logger.error(f"Error getting last use timestamp for user data directory {user_uuid}: {e}")
                            continue
                        if last_use_file_content is None:
                            raise Exception(f"Last use timestamp for user data directory {user_uuid} is not set, this should not happen")
                        last_use_timestamp = datetime.fromisoformat(last_use_file_content)
                        # Check if the last use timestamp is more than MOUNTED_USER_DATA_DIR_CACHE_TIME_SECONDS ago
                        if last_use_timestamp < datetime.now() - timedelta(seconds=MOUNTED_USER_DATA_DIR_CACHE_TIME_SECONDS):
                            logger.info(f"Unmounting user data directory {user_uuid} because it has not been used for more than {MOUNTED_USER_DATA_DIR_CACHE_TIME_SECONDS} seconds")
                            # Unmount the user data directory
                            unmount_user_data_dir(user_uuid)
                except Exception as e:
                    logger.error(f"Error cleaning up unmounted user data for user {user_uuid}, continuing the the next user data directory: {e}")
    except Exception as e:
        logger.error(f"Error cleaning up unmounted user data directories, restarting the loop any way: {e}")
        # Restart the loop
        # Get the current asyncio event loop
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(cleanup_mounted_user_data_dir_loop(logger))
        else:
            asyncio.run(cleanup_mounted_user_data_dir_loop(logger))



@contextmanager
def mount_user_data_dir_dependency(user_uuid: str):
    """
    Mount the user data directory
    """
    current_timestamp_iso_str = None
    try:
        # Add a lock to the user data directory and maintain it until this request is finished to avoid race conditions
        # TODO Add a per file lock instead for more granularity and efficiency
        user_data_dir_lock = FileLock(USER_DATA_DIR_LOCK_PATH.format(user_uuid=user_uuid), timeout=15) # ?
        with user_data_dir_lock:

            # Check if the user data directory is already mounted
            if not os.path.exists(USER_DATA_FOLDER_PATH.format(user_uuid=user_uuid)):
                mount_user_data_dir(user_uuid)
            else:
                logger.debug(f"User data directory for user {user_uuid} is already mounted, skipping the mount")

            yield
    
    except Exception as e:
        logger.error(f"Error mounting user data directory for user {user_uuid}: {e}")
        raise e
    finally:
        # Write the current timestamp to the lock timestamp file so that we know when the last use of it was to unmount it if needed by the cleanup_unmounted_user_data_dir_loop
        current_timestamp_iso_str = datetime.now().isoformat()
        # Overwrite the lock timestamp file with the current timestamp
        with open(USER_DATA_DIR_LAST_USE_TIMESTAMP_PATH.format(user_uuid=user_uuid), "w") as f:
            f.write(current_timestamp_iso_str)
    

def mount_user_data_dir(user_uuid: str):
    """
    Mount the user data directory
    """
    try:
        logger.info(f"Mounting user data directory for user {user_uuid}")
        if os.environ.get("DEPLOYMENT_TYPE") == "hosted":
            # If the folder already exist, raise an error as this should not happen
            if os.path.exists(USER_DATA_FOLDER_PATH.format(user_uuid=user_uuid)):
                raise Exception(f"User data directory for user {user_uuid} already exists, this should not happen")
            # Try to mount the user data directory by getting the pvc for this user_uuid and mounting it using kubernetes_client
            #configuration = get_kubernetes_config()
            mount_user_data_dir_hosted(user_uuid)
        # Else if the deployment type is self-hosted
        else:
            mount_user_data_dir_self_hosted(user_uuid)
    except Exception as e:
        logger.error(f"Error mounting user data directory for user {user_uuid}: {e}")
        raise e
    
def mount_user_data_dir_self_hosted(user_uuid: str):
    try:
        if not os.path.exists(USER_DATA_FOLDER_PATH.format(user_uuid=user_uuid)):
            # Create the user data directory
            os.makedirs(USER_DATA_FOLDER_PATH.format(user_uuid=user_uuid), exist_ok=True)
        #else:
            # User data directory already exist and is accessible in the user-data volume at /data/{user_uuid}
    except Exception as e:
        logger.error(f"Error mounting user data directory for user {user_uuid}: {e}")
        raise e


def mount_user_data_dir_hosted(user_uuid: str) -> bool:
    """
    Mount the user data directory for the hosted deployment type
    """
    try:
        # Load the kubernetes config
        config.load_incluster_config()
        # Enter a context with an instance of the API kubernetes.client
        with client.CoreV1Api() as api_instance:
            pvc_exists = None
            read_pvc_api_response = api_instance.read_namespaced_persistent_volume_claim(
                name=f"user-data-{user_uuid}",
                namespace="idapt"
            )
            logger.debug(f" read_namespaced_persistent_volume_claim api_response: {read_pvc_api_response}")
            #TODO Check if the pvc is already mounted
            if read_pvc_api_response is not None and read_pvc_api_response.status == 200 and read_pvc_api_response.metadata.name == f"user-data-{user_uuid}":
                pvc_exists = True
            elif read_pvc_api_response is not None and read_pvc_api_response.status == 404:
                # If the pvc do not exist, create it
                pvc_exists = False
            else:
                raise Exception(f"Error mounting user data directory for user {user_uuid}: {read_pvc_api_response}")
            if not pvc_exists:
                # TODO maybe add the user_uuid to the pv metadata ?
                # If the pvc do not exist, create it
                create_pvc_api_response = api_instance.create_namespaced_persistent_volume_claim(
                    body=client.V1PersistentVolumeClaim(
                        api_version="v1",
                        metadata=client.V1ObjectMeta(
                            name=f"user-data-{user_uuid}",
                            labels={"app": "idapt", "user_uuid": user_uuid}
                        ),
                        spec=client.V1PersistentVolumeClaimSpec(
                            storage_class_name="user-data-sc",
                            access_modes=["ReadWriteOnce"],
                            resources=client.V1ResourceRequirements(
                                requests={"storage": "1Gi"}
                            )
                        )
                    ),
                    namespace="idapt"
                )
                logger.debug(f" create_namespaced_persistent_volume_claim api_response: {create_pvc_api_response}")
                if create_pvc_api_response is None or create_pvc_api_response.status != 201:
                    raise Exception(f"Error creating user data directory for user {user_uuid}: {create_pvc_api_response}")
                
            # Get the current pod name
            current_pod_name = os.environ.get("POD_NAME", None)
            if current_pod_name is None:
                raise Exception("POD_NAME is not set, this is not running a kubernetes pod")
            
            # Bind the pvc to the pod and mount it to the /data/{user_uuid} folder
            mount_pvc_api_response = api_instance.patch_namespaced_pod(
                name=current_pod_name,
                namespace="idapt",
                body=client.V1Pod(
                    spec=client.V1PodSpec(
                        volumes=[
                            client.V1Volume(
                                name=f"user-data-{user_uuid}",
                                persistent_volume_claim=client.V1PersistentVolumeClaimVolumeSource(claim_name=f"user-data-{user_uuid}")
                            )
                        ],
                        containers=[
                            client.V1Container(
                                name=f"idapt-backend",
                                volume_mounts=[
                                    client.V1VolumeMount(
                                        name=f"user-data-{user_uuid}", 
                                        mount_path=USER_DATA_FOLDER_PATH.format(user_uuid=user_uuid)
                                    )
                                ]
                            )
                        ]
                    )
                )
            )

            if mount_pvc_api_response is not None and mount_pvc_api_response.status == 200:
                return True
            else:
                raise Exception(f"Error mounting user data directory for user {user_uuid}: {mount_pvc_api_response}")
    except ApiException as e:
        logger.error(f"Error mounting user data directory for user {user_uuid}: {e}")
        raise e
    except Exception as e:
        logger.error(f"Error mounting user data directory for user {user_uuid}: {e}")
        raise e
    
def unmount_user_data_dir(user_uuid: str):
    """
    Unmount the user data directory
    """
    try:
        logger.info(f"Unmounting user data directory for user {user_uuid}")
        if os.environ.get("DEPLOYMENT_TYPE") == "hosted":
            unmount_user_data_dir_hosted(user_uuid)
        else:
            unmount_user_data_dir_self_hosted(user_uuid)
    except Exception as e:
        logger.error(f"Error unmounting user data directory for user {user_uuid}: {e}")
        raise e
    
def unmount_user_data_dir_hosted(user_uuid: str):
    """
    Unmount the user data directory for the hosted deployment type
    """
    try:
        # Load the kubernetes config
        config.load_incluster_config()
        # Enter a context with an instance of the API kubernetes.client
        with client.CoreV1Api() as api_instance:
            # Get the current pod name
            current_pod_name = os.environ.get("POD_NAME", None)
            if current_pod_name is None:
                raise Exception("POD_NAME is not set, this is not running a kubernetes pod")
            
            # Get the current pod
            current_pod = api_instance.read_namespaced_pod(
                name=current_pod_name,
                namespace="idapt"
            )
            logger.debug(f" current_pod: {current_pod}")
            # Get the list of current volumes mounted in the pod
            current_volumes = current_pod.spec.volumes
            logger.debug(f" current_volumes: {current_volumes}")
            # Get the list of current volume mounts in the pod
            current_volume_mounts = current_pod.spec.containers[0].volume_mounts
            logger.debug(f" current_volume_mounts: {current_volume_mounts}")
            # Remove the volume mount for this user from the list of current volume mounts
            current_volume_mounts_without_this_user = [volume_mount for volume_mount in current_volume_mounts if volume_mount.name != f"user-data-{user_uuid}"]
            logger.debug(f" current_volume_mounts after removing the user data directory volume mount: {current_volume_mounts_without_this_user}")
            # Remove the volume for this user from the list of current volumes
            current_volumes_without_this_user = [volume for volume in current_volumes if volume.name != f"user-data-{user_uuid}"]
            logger.debug(f" current_volumes after removing the user data directory volume: {current_volumes_without_this_user}")

            # Unbind the pvc from the pod, only include the fields that are needed to be patched
            api_instance.patch_namespaced_pod(
                name=f"{current_pod_name}",
                namespace="idapt",
                body=client.V1Pod(
                    spec=client.V1PodSpec(
                        volumes=current_volumes_without_this_user,
                        containers=[
                            client.V1Container(
                                name=f"idapt-backend",
                                volume_mounts=current_volume_mounts_without_this_user # Keep the volume_mounts
                            )
                        ]
                    )
                )
            )
    except Exception as e:
        logger.error(f"Error unmounting user data directory for user {user_uuid}: {e}")
        raise e
    
def unmount_user_data_dir_self_hosted(user_uuid: str):
    """
    Unmount the user data directory for the self-hosted deployment type
    """
    try:
        # Do nothing
        pass
    except Exception as e:
        logger.error(f"Error unmounting user data directory for user {user_uuid}: {e}")
        raise e
            
def get_kubernetes_config():
    """
    Get the kubernetes config
    """
    try:
        configuration = client.Configuration()
        # Configure API key authorization: BearerToken
        kubernetes_pod_service_account_token = os.environ.get("KUBERNETES_POD_SERVICE_ACCOUNT_TOKEN", None)
        if kubernetes_pod_service_account_token is None:
            raise Exception("KUBERNETES_POD_SERVICE_ACCOUNT_TOKEN is not set, it is needed when using the hosted deployment type")
        configuration.api_key['authorization'] = kubernetes_pod_service_account_token
        # Uncomment below to setup prefix (e.g. Bearer) for API key, if needed
        # configuration.api_key_prefix['authorization'] = 'Bearer'

        # Defining host is optional and default to http://localhost
        configuration.host = "http://localhost"
        
        return configuration
    except Exception as e:
        logger.error(f"Error getting kubernetes config: {e}")
        raise e
