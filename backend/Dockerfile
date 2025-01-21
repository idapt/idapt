# Build stage
FROM python:3.13-bookworm AS backend-build

# Install Python and required packages
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install poetry with curl as recommended by poetry, use version 2.0.0, install it in /opt/poetry
# Add poetry to the path
RUN curl -sSL https://install.python-poetry.org | POETRY_HOME=/opt/poetry POETRY_VERSION=2.0.0 python3 - && \
    cd /usr/local/bin && \
    ln -s /opt/poetry/bin/poetry

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

WORKDIR /backend

# Copy only the poetry files to the build image necessary for poetry to install the dependencies
COPY ./pyproject.toml ./poetry.lock ./
RUN touch README.md

# Install Poetry and dependencies
RUN --mount=type=cache,target=$POETRY_CACHE_DIR poetry install --without dev --no-root



# Release stage
FROM python:3.13-slim-bookworm AS release

# Install openssl
RUN apt-get update && apt-get install -y \
    openssl \
    && rm -rf /var/lib/apt/lists/*

ENV VIRTUAL_ENV=/backend/.venv \
    PATH="/backend/.venv/bin:$PATH"

# Copy the virtual environment to the release image
COPY --from=backend-build ${VIRTUAL_ENV} ${VIRTUAL_ENV}

# Copy the backend code to the release image
COPY ./ /backend


# Run the backend on startup
CMD [ "sh", "-c", "python /backend/main.py"]