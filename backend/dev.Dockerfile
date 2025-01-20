#FROM python:3.11-buster AS builder
#
#RUN pip install poetry==2.0.0
#
#ENV POETRY_NO_INTERACTION=1 \
#    POETRY_VIRTUALENVS_IN_PROJECT=1 \
#    POETRY_VIRTUALENVS_CREATE=1 \
#    POETRY_CACHE_DIR=/tmp/poetry_cache
#
#WORKDIR /app
#
#COPY pyproject.toml poetry.lock ./
#RUN touch README.md
#
#RUN --mount=type=cache,target=$POETRY_CACHE_DIR poetry install --without dev --no-root
#
#FROM python:3.11-slim-buster AS runtime
#
#ENV VIRTUAL_ENV=/app/.venv \
#    PATH="/app/.venv/bin:$PATH"
#
#COPY --from=builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}
#
##COPY ./backend ./backend
#
#ENTRYPOINT ["python", "/app/backend/main.py"]


# Container build script
FROM python:3.13 AS backend-build

# Install all the poetry dependencies in a separate directory
WORKDIR /poetry-install

ENV PYTHONPATH=/poetry-install

# Install openssl
RUN apt-get update && apt-get install -y openssl && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | POETRY_HOME=/opt/poetry POETRY_VERSION=2.0.0 python3 - && \
    cd /usr/local/bin && \
    ln -s /opt/poetry/bin/poetry && \
    poetry config virtualenvs.create false

# Install Chromium for web loader
# Can disable this if you don't use the web loader to reduce the image size
# Not used for now
# RUN apt update && apt install -y chromium chromium-driver 

# Install dependencies with poetry
COPY ./pyproject.toml ./poetry.lock* /poetry-install/

RUN poetry install --no-interaction --no-root

# Set the working directory to the backend directory.
WORKDIR /backend


# Run the dev backend server
CMD ["python", "main.py"]

# Keep the container running, you can use this if you want to manually exec into the container for dev.
#CMD ["tail", "-f", "/dev/null"