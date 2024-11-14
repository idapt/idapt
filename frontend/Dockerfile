# Use the node image only to build the application.
FROM node:20-alpine AS build

WORKDIR /frontend

# Install dependencies
COPY package.json package-lock.* ./
RUN npm install

# Build the application
COPY . .
RUN npm run build

# ====================================
# Use the nginx image to serve the built application.
FROM nginx:alpine

# Copy the built app
COPY --from=build /frontend/out /usr/share/nginx/html
# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Run at built container start
# Run the nginx server to serve the built next.js application
CMD ["nginx", "-g", "daemon off;"]