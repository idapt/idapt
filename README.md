<picture>
  <source media="(prefers-color-scheme: dark)" srcset="./assets/idapt_logo_dark_transparent.png">
  <source media="(prefers-color-scheme: light)" srcset="./assets/idapt_logo_light_transparent.png">
  <img alt="Idapt Logo" src="./assets/idapt_logo_dark_transparent.png" width="200">
</picture>

**[Idapt](https://idapt.ai) is an app that allows you to own and augment your personal data using AI.**

Go to the [website](https://idapt.ai) for more information.

This project is open source and you are welcome to contribute to it.


# Getting Started

## Production Installation

Clone the repository with `git clone https://github.com/idapt/idapt.git`.
Run `docker compose up --build` to start the production server.
This will build the production images and start the containers in production mode.
You can then access the frontend at [http://localhost:3030](http://localhost:3030).

## Development Installation

In development mode, the frontend and backend folders are synced with the host folders so any changes you make to the code will be reflected directly in the containers.
The containers ports are also exposed to facilitate development.

### Start the containers

Clone the repository with `git clone https://github.com/idapt/idapt.git`.
Run `docker compose -f dev.docker-compose.yml up --build` to start the development server.
This will start all the containers in development mode and sync the code changes between the host and the frontend and backend containers.

### Start the backend

Run `docker exec -it idapt-backend /bin/sh` to get a shell into the backend container
Run `python main.py` to start the backend. 
You can access the backend if needed at [http://localhost:3030/api](http://localhost:3030/api).
*The poetry dependencies are already installed in the container following the `pyproject.toml` file.*

### Start the frontend

Run `docker exec -it idapt-frontend /bin/sh` to get a shell into the frontend container 
Run `npm run dev` to start the frontend. 
You can then access the frontend at http://localhost:3030.
*The node_modules are synced with the host.*

*Note that the developement stack and the production use different docker storage volumes.*

## Acknowledgements

This app uses the open source project LlamaIndex, here is their github if you want to contribute there : [LlamaIndex](https://github.com/run-llama/llama_index).