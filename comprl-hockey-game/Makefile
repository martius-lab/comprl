# Basic commands for starting/stopping the application via docker
.PHONY: build up down logs reload

build:
	COMPOSE_BAKE=true docker compose build

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f

# reload configuration
reload:
	docker compose kill --signal=SIGHUP game-server
