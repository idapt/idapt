# Build stage
FROM node:23-alpine AS build

WORKDIR /frontend

# Install dependencies
COPY package.json package-lock.* ./
RUN npm install

# Build the application
COPY . .
RUN npm run build

# =====================
# Runtime stage - use a minimal static file server
FROM node:23-alpine

WORKDIR /app

# Copy only the built files
COPY --from=build /frontend/out ./out

# Install serve for static file serving
RUN npm install -g serve

# Run with minimal privileges
USER node

# Serve the static files
CMD ["serve", "-s", "out", "-l", "3000"]