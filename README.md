## Production

Run `docker compose up --build` to start the production server.
This will build the production images and start the containers in production mode.
You can then access the frontend at http://localhost:3000.

## Development

### Start the containers

Run `docker compose -f dev.docker-compose.yml up --build` to start the development server.
This will start all the containers in development mode and sync the code changes between the host and the frontend and backend containers.

### Start the backend

Then you can run `docker exec -it idapt-backend /bin/sh` to get a shell into the backend container and run `python main.py` to start the backend. 
You can access the backend if needed at http://localhost:8000.
*The poetry dependencies are already installed in the container.*

### Start the frontend

Run `docker exec -it idapt-frontend /bin/sh` to get a shell into the frontend container and run `npm run dev` to start the frontend. 
You can then access the frontend at http://localhost:3000.
*The node_modules are synced with the host.*

*Note that the developement stack and the production use different docker storage volumes.*
