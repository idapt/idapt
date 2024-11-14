# Build the backend image
FROM python:3.11 AS build

WORKDIR /backend

ENV PYTHONPATH=/backend

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | POETRY_HOME=/opt/poetry python && \
    cd /usr/local/bin && \
    ln -s /opt/poetry/bin/poetry && \
    poetry config virtualenvs.create false

# Install Chromium for web loader
# Can disable this if you don't use the web loader to reduce the image size
# Not used for now
# RUN apt update && apt install -y chromium chromium-driver 

# Install dependencies
COPY ./pyproject.toml ./poetry.lock* /backend/
RUN poetry install --no-root --no-cache --only main

# ====================================
# Release image
# ====================================
FROM build AS release

COPY . .

# Run at built container start

# Run the backend
CMD ["python", "main.py"]