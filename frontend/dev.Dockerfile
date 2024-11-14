# Container build script
FROM node:20-alpine

WORKDIR /frontend


# Run at built container start

# Install dependencies if not already installed on the host
#CMD ["npm", "install"]

# Run the dev server
CMD sh -c "npm install && npm run dev"

# Keep the container running, you can use this if you want to manually exec into the container for dev.
#CMD ["tail", "-f", "/dev/null"]