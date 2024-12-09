#!/bin/sh

# This is useful in case the nginx container stops and loose the variable values. # TODO: Treat ollama custom host as a host and store it in the host file ?
# No need to wait for the backend to be ready as if it is not up, it will start soon and set the ollama host in nginx at its startup.
# Try to fetch ollama host from backend with a short timeout to avoid blocking the startup of the nginx container.
echo "Trying to fetch ollama host from backend..."
OLLAMA_HOST=$(wget -q -O - --timeout=1 http://idapt-backend:8000/api/settings 2>/dev/null | grep -o '"custom_ollama_llm_host":"[^"]*' | cut -d'"' -f4)

if [ ! -z "$OLLAMA_HOST" ]; then
    # Create a temporary config file with the fetched host
    echo "map \$uri \$ollama_target_host { default \"$OLLAMA_HOST\"; }" > /etc/nginx/ollama_host.conf
    echo "Setting ollama host at nginx startup: $OLLAMA_HOST"
else
    # Use default host if backend is not available
    echo "map \$uri \$ollama_target_host { default \"http://host.docker.internal:11434\"; }" > /etc/nginx/ollama_host.conf
    echo "Setting custom ollama host at nginx startup to default: http://host.docker.internal:11434"
fi

# Start nginx
echo "Starting nginx..."
exec nginx -g 'daemon off;'
