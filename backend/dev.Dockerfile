FROM python:3.11

# Install all the poetry dependencies in a separate directory
WORKDIR /poetry-install

ENV PYTHONPATH=/poetry-install

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
COPY ./pyproject.toml ./poetry.lock* /poetry-install/
RUN poetry install


# Set the working directory to the backend directory.
WORKDIR /backend

# Keep the container running
CMD ["tail", "-f", "/dev/null"]