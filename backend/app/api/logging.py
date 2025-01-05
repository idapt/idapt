import logging
import os

def configure_app_logging():

  environment = os.getenv("ENVIRONMENT", "prod")  # Default to 'prod' if not set so that we dont risk exposing the API to the public

  if environment == "dev":
      # Configure more verbose logging for development
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(levelname)s: %(message)s'
    )
    # Set log levels for other specific loggers
    logging.getLogger('uvicorn').setLevel(logging.DEBUG)
    logging.getLogger('sqlalchemy').setLevel(logging.WARNING)
    logging.getLogger('alembic').setLevel(logging.WARNING)

  else:
      # Keep detailed logging for production for now
      logging.basicConfig(
          level=logging.INFO,
          format='%(levelname)s: %(message)s'
      )
      # Set log levels for specific loggers
      logging.getLogger('uvicorn').setLevel(logging.INFO)
      logging.getLogger('sqlalchemy').setLevel(logging.WARNING)
      logging.getLogger('alembic').setLevel(logging.WARNING)

    # Filter out health check logs from uvicorn
    #logging.getLogger("uvicorn.access").addFilter(
    #    lambda record: "/api/health" not in record.getMessage()
    #)
