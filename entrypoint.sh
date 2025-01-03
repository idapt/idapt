#!/bin/bash
# Set the script to exit on error
set -e

# Start nginx as nginx user with output redirection
echo "Starting nginx"
su -s /bin/sh -c "/nginx-entrypoint.sh 2>&1 | sed 's/^/[nginx] /'" nginx &

# Start backend as backend user with output redirection 
# CMD ["poetry", "run", "python", "/backend/main.py"]
echo "Starting backend"
su -s /bin/sh -c "/backend-entrypoint.sh | sed 's/^/[backend] /'" backend &

# Wait for any process to exit
echo "Waiting for processes..."
wait -n

# Exit with status of process that exited first
exit $?