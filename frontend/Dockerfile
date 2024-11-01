FROM node:20-alpine AS build

WORKDIR /frontend

# Install dependencies
COPY package.json package-lock.* ./
RUN npm install

# Build the application
COPY . .
RUN npm run build

# ====================================
FROM build AS release
RUN npm install -g serve

CMD ["serve", "-s", "out"]