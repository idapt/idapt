# Use the official Node.js image as the base image
FROM node:20

# Install PostgreSQL client utilities
RUN apt-get update && apt-get install -y postgresql-client

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy package.json and package-lock.json to the working directory
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy the rest of the application code to the working directory
COPY . .

# Copy the wait script into the container
COPY wait-for-postgres.sh /usr/local/bin/wait-for-postgres.sh
RUN chmod +x /usr/local/bin/wait-for-postgres.sh

# Set environment variables for the wait script
ENV POSTGRES_HOST=postgres
ENV POSTGRES_PORT=5432
ENV POSTGRES_USER=${DATABASE_USERNAME}

# Use the wait script to ensure the database is ready before running Prisma
CMD sh -c "wait-for-postgres.sh && npx prisma generate && npx prisma db push && npm run dev"

# Expose the port the app runs on inside the container
EXPOSE 3000
