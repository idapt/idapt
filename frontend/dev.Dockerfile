FROM node:20-alpine

WORKDIR /frontend

# Keep the container running
CMD ["tail", "-f", "/dev/null"]