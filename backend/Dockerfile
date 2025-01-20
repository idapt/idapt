# Build stage
FROM python:3.13-bookworm AS backend-build

# Install Python and required packages
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Add python to the path and create symlink for python command
#RUN ln -s /usr/bin/python3 /usr/bin/python
#ENV PATH=/usr/bin:$PATH

# Install poetry with curl as recommended by poetry, use version 2.0.0, install it in /opt/poetry
# Add poetry to the path
RUN curl -sSL https://install.python-poetry.org | POETRY_HOME=/opt/poetry POETRY_VERSION=2.0.0 python3 - && \
    cd /usr/local/bin && \
    ln -s /opt/poetry/bin/poetry


WORKDIR /backend
#ENV PYTHONPATH=/backend

# Install Poetry and dependencies
#COPY ./backend/pyproject.toml ./backend/poetry.lock ./backend/poetry.toml ./
# Copy backend code
COPY ./ /backend
# Install dependencies
RUN cd /backend && \
    poetry install --no-interaction --no-root


# Release stage
FROM python:3.13-bookworm AS release

# Install python
RUN apt-get update && apt-get install -y \
    curl \
    openssl \
    && rm -rf /var/lib/apt/lists/*

# Already exist in the nginx certbot image
#RUN ln -s /usr/bin/python3.11 /usr/bin/python
# Install poetry with curl as recommended by poetry, use version 2.0.0, install it in /opt/poetry # TODO Find a way to not use poetry in the release image
# Add poetry to the path
RUN curl -sSL https://install.python-poetry.org | POETRY_HOME=/opt/poetry POETRY_VERSION=2.0.0 python3 - && \
    cd /usr/local/bin && \
    ln -s /opt/poetry/bin/poetry


# Copy the virtual environment and the backend code to the release image
COPY --from=backend-build --chown=backend:backend /backend /backend

WORKDIR /backend

CMD ["poetry", "run", "python", "main.py"]

# Keep the container running, you can use this if you want to manually exec into the container for dev.
#CMD ["tail", "-f", "/dev/null"]



#FROM python:3.13-bookworm AS builder
#
#RUN apt-get update && apt-get install -y \
#    curl \
#    && rm -rf /var/lib/apt/lists/*
#
#RUN curl -sSL https://install.python-poetry.org | POETRY_HOME=/opt/poetry POETRY_VERSION=2.0.0 python3 - && \
#    cd /usr/local/bin && \
#    ln -s /opt/poetry/bin/poetry
#
#ENV POETRY_NO_INTERACTION=1 \
#    POETRY_VIRTUALENVS_IN_PROJECT=1 \
#    POETRY_VIRTUALENVS_CREATE=1 \
#    POETRY_CACHE_DIR=/tmp/poetry_cache
#
#WORKDIR /backend
#
#COPY pyproject.toml poetry.lock ./
#RUN touch README.md
#
#RUN --mount=type=cache,target=$POETRY_CACHE_DIR poetry install --without dev --no-root
#
#RUN poetry show
#
#FROM python:3.13-slim-bookworm AS runtime
#
#ENV VIRTUAL_ENV=/backend/.venv \
#    PATH="/backend/.venv/bin:$PATH"
#
#COPY --from=builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}
#
#RUN python -V
#RUN python -c 'help("modules")'
#
#COPY ./ /backend
#
#WORKDIR /backend
#
#CMD ["python", "-c", "help('modules')"]
