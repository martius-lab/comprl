# Basic commands for starting/stopping the application via docker
.PHONY: build up down logs reload

build:
	COMPOSE_BAKE=true docker compose build

up-server:
	docker compose up -d game_server

up-bots:
	docker compose up -d bot_agent_strong bot_agent_weak

stop-bots:
	docker compose stop bot_agent_strong bot_agent_weak

down:
	docker compose down

logs:
	docker compose logs -f

# reload configuration
reload:
	docker compose kill --signal=SIGHUP game_server
