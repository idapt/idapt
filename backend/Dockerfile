# Build stage
FROM debian:bookworm-slim AS backend-build

# Install Python and required packages
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3-pip \
    python3.11-venv \
    python3-poetry \
    && rm -rf /var/lib/apt/lists/*

# Add python to the path and create symlink for python command
RUN ln -s /usr/bin/python3.11 /usr/bin/python
#ENV PATH=/usr/bin:$PATH


WORKDIR /backend
#ENV PYTHONPATH=/backend

# Install Poetry and dependencies
COPY ./backend/pyproject.toml ./backend/poetry.lock ./backend/poetry.toml ./
RUN poetry config virtualenvs.in-project true && \
    poetry install --only main --no-root

# Copy application code and install project
COPY ./backend/ /backend
RUN cd /backend && poetry install --only main

# Release stage
FROM debian:bookworm-slim AS release

# Install python
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3-pip \
    python3-virtualenv \
    python3-poetry \
    && rm -rf /var/lib/apt/lists/*

# Add python to the path
#ENV PATH=/usr/local/bin:$PATH
RUN ln -s /usr/bin/python3.11 /usr/bin/python

# Copy the virtual environment and the backend code to the release image
COPY --from=backend-build /backend /backend

# Copy the entrypoint script and make it executable
RUN chmod +x /backend/entrypoint.sh

# Set the entrypoint script as the entrypoint for the container
ENTRYPOINT ["/backend/entrypoint.sh"]

# Keep the container running, you can use this if you want to manually exec into the container for dev.
#CMD ["tail", "-f", "/dev/null"]