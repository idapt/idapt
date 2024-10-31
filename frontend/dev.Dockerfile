FROM node:20-alpine

# Set the working directory to the frontend directory.
WORKDIR /frontend

# Keep the container running
CMD ["tail", "-f", "/dev/null"]