# Build frontend
FROM node:23-alpine AS frontend-build
WORKDIR /frontend-build
COPY frontend/package.json frontend/package-lock.* ./
RUN npm install
COPY frontend/ .
RUN npm run build



# Build backend
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




# Final stage
FROM jonasal/nginx-certbot:5.4.0 AS release


# Create users and groups
RUN groupadd -r backend && useradd -r -g backend backend
# Nginx already exists in the nginx-certbot image

# Install required packages for nginx
RUN apt-get update && apt-get install -y \
    gettext
#    python3 \
#    python3-pip \
#    && rm -rf /var/lib/apt/lists/*

# Create all required nginx directories with proper permissions
RUN mkdir -p /var/cache/nginx && \
    mkdir -p /var/cache/nginx/client_temp && \
    mkdir -p /var/cache/nginx/proxy_temp && \
    mkdir -p /var/cache/nginx/fastcgi_temp && \
    mkdir -p /var/cache/nginx/uwsgi_temp && \
    mkdir -p /var/cache/nginx/scgi_temp && \
    mkdir -p /tmp && \
    chown -R nginx:nginx /var/cache/nginx && \
    chown -R nginx:nginx /tmp && \
    chmod 1777 /tmp
# TODO Remove tmp
# Create symlink for python command
#RUN ln -s /usr/bin/python3 /usr/bin/python

# Copy nginx config
RUN mkdir -p /nginx-config-source
COPY nginx/config/ /nginx-config-source/
RUN chmod 775 /nginx-config-source/* && \
    chown -R nginx:nginx /nginx-config-source

# Copy user provided nginx ssl certificates
RUN mkdir -p /nginx-certs-source
COPY nginx/certs/ /nginx-certs-source/
RUN find /nginx-certs-source -type f -exec chmod 775 {} + || true && \
    chown -R nginx:nginx /nginx-certs-source

# Copy frontend static files
COPY --from=frontend-build --chown=nginx:nginx /frontend-build/out /usr/share/nginx/html




# Backend
#FROM debian:bookworm-slim AS release

# Remove any existing python installation
#RUN apt-get update && apt-get purge -y python

# Install python
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3-pip \
    python3-virtualenv \
    python3-poetry \
    && rm -rf /var/lib/apt/lists/*

# Add python to the path
#ENV PATH=/usr/local/bin:$PATH
# Already exist in the nginx certbot image
RUN ln -s /usr/bin/python3.11 /usr/bin/python

# Copy the virtual environment and the backend code to the release image
COPY --from=backend-build --chown=backend:backend /backend /backend
#WORKDIR /backend
#ENV PYTHONPATH=/backend
#RUN chown -R backend:backend /backend

# Make the entrypoint script executable
#RUN chmod +x /backend/entrypoint.sh

# Set the entrypoint script as the entrypoint for the container
#ENTRYPOINT ["/backend/entrypoint.sh"]

# Keep the container running, you can use this if you want to manually exec into the container for dev.
#CMD ["tail", "-f", "/dev/null"]









# Copy the 3 entrypoint scripts and make them executable
COPY nginx/entrypoint.sh /nginx-entrypoint.sh
COPY backend/entrypoint.sh /backend-entrypoint.sh
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /nginx-entrypoint.sh && \
    chmod +x /backend-entrypoint.sh && \
    chmod +x /entrypoint.sh



# Create required directories with proper permissions
RUN mkdir -p /var/www/letsencrypt && \
    mkdir -p /etc/letsencrypt && \
    mkdir -p /var/log/nginx && \
    mkdir -p /backend_data && \
    mkdir -p /data && \
    chown -R nginx:nginx /var/www/letsencrypt && \
    chown -R nginx:nginx /etc/letsencrypt && \
    chown -R nginx:nginx /var/log/nginx && \
    chown -R nginx:nginx /etc/nginx && \
    chown -R backend:backend /backend_data && \
    chown -R backend:backend /data


# Add volume mount points metadata
VOLUME ["/etc/letsencrypt", "/backend_data", "/data"]


# Add exposed ports metadata
EXPOSE 80 443


# Set the entrypoint
ENTRYPOINT ["/entrypoint.sh"]