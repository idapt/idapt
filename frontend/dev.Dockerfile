# Container build script
FROM node:23-alpine

WORKDIR /frontend

# Set the startup command to run the dev server
CMD sh -c "npm install && npm run dev" 
# Remove install ?

# Keep the container running, you can use this if you want to manually exec into the container for dev.
#CMD ["tail", "-f", "/dev/null"]