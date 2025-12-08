# Basic commands for starting/stopping the application via docker
.PHONY: build up down logs reload

build:
	COMPOSE_BAKE=true docker compose build

up-server:
	docker compose up -d gameserver

up-bots:
	docker compose up -d strongbot weakbot

stop-bots:
	docker compose stop strongbot weakbot

down:
	docker compose down

logs:
	docker compose logs -f

# reload configuration
reload:
	docker compose kill --signal=SIGHUP gameserver
