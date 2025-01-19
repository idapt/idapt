<picture>
  <source media="(prefers-color-scheme: dark)" srcset="./assets/idapt_logo_dark_transparent.png">
  <source media="(prefers-color-scheme: light)" srcset="./assets/idapt_logo_light_transparent.png">
  <img alt="Idapt Logo" src="./assets/idapt_logo_dark_transparent.png" width="200">
</picture>

**[idapt](https://idapt.ai) allows you to create your own personal AI by regrouping your data from multiple sources (Files, Emails, Google Drive, etc.) and allow your AI assistant to use it in your chats to provide a fully personalized experience.**

You can choose to host it yourself or use our hosted version at [idapt.ai](https://idapt.ai) that uses confidential computing and encryption to ensure that only you can access your data.

Your data is completely encrypted on our servers so that even we cannot access it and the project is open source for complete transparency.

Go to the [website](https://idapt.ai) for more information.

**THE APP IS STILL AT A VERY EARLY STAGE AND BUGS ARE TO BE EXPECTED, ALWAYS BACKUP YOUR DATA ELSEWHERE TO PREVENT DATA LOSS UNTIL THE APP IS MORE STABLE.**

# Getting Started

## Production Installation

- Install [Docker](https://docs.docker.com/get-started/get-docker/).
- Run this command to clone the repository in your current directory and start the production server locally.
```bash
git clone https://github.com/idapt/idapt.git && cd idapt && sudo docker compose up --build
```
- Access the app at [https://localhost](https://localhost).
- Add your data sources, setup your settings (model provider, system prompt, etc.) and start chatting with your private, personal AI assistant !

### Model Provider
You can use any hosted model provider that you want or use ollama for local inference, you will need to have [Ollama](https://ollama.com/) running on your machine **(at default port 11434 and with the default 0.0.0.0 host)** or on a remote server. We will soon propose a private hosted alternative so that you can run more powerful models.

### Security
The local server version of the app do not have any authentication system and is only meant to be used locally with localhost behind a safe firewall. Authentication and encryption is coming soon.

## Development Installation

In development mode, the frontend and backend folders are synced with the host folders so any changes you make to the code will be reflected directly in the containers.
The containers ports are also exposed to facilitate development.

- Clone the repository with 
```bash
git clone https://github.com/idapt/idapt.git && cd idapt
```
- Run 
```bash
docker compose -f dev.local.docker-compose.yml up --build
```
in the idapt root folder to start the development server.
*This will start all the containers in development mode and sync the code changes between the host and the frontend and backend containers.*
- Access the app at [https://localhost](https://localhost).
- Build or fix !

Development notes :
*The poetry dependencies are already installed in the container following the `pyproject.toml` file at build time.*
*The node_modules are synced with the host.*
*The developement stack and the production use different docker storage volumes as the compose name is different.*

## Architecture

See the compose file for more details on the architecture.
- FastAPI Python backend
- NextJS React frontend
- SQLite database
- Chroma vector database
- Nginx for reverse proxy routing

The local version do not have any authentication system.