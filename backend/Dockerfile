# Build stage
FROM debian:bookworm-slim AS backend-build

# Install Python and required packages
RUN apt-get update && apt-get install -y \
    python3.13 \
    python3.13-venv \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Add python to the path and create symlink for python command
RUN ln -s /usr/bin/python3.13 /usr/bin/python
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
FROM debian:bookworm-slim AS release

# Install python
RUN apt-get update && apt-get install -y \
    python3.13 \
    python3.13-venv \
    curl \
    openssl \
    && rm -rf /var/lib/apt/lists/*

# Already exist in the nginx certbot image
RUN ln -s /usr/bin/python3.11 /usr/bin/python
# Install poetry with curl as recommended by poetry, use version 2.0.0, install it in /opt/poetry # TODO Find a way to not use poetry in the release image
# Add poetry to the path
RUN curl -sSL https://install.python-poetry.org | POETRY_HOME=/opt/poetry POETRY_VERSION=2.0.0 python3 - && \
    cd /usr/local/bin && \
    ln -s /opt/poetry/bin/poetry


# Copy the virtual environment and the backend code to the release image
COPY --from=backend-build --chown=backend:backend /backend /backend

# Copy the entrypoint script and make it executable
RUN chmod +x /backend/entrypoint.sh

# Set the entrypoint script as the entrypoint for the container
ENTRYPOINT ["/backend/entrypoint.sh"]

# Keep the container running, you can use this if you want to manually exec into the container for dev.
#CMD ["tail", "-f", "/dev/null"]