.PHONY: $(MAKECMDGOALS)
MAKEFLAGS += --no-print-directory
##
##  🚧 DipDup developer tools
##
PACKAGE=defi_space_indexer
TAG=latest
COMPOSE=deploy/compose.yaml
ENV_FILE=.env

help:           ## Show this help (default)
	@grep -Fh "##" $(MAKEFILE_LIST) | grep -Fv grep -F | sed -e 's/\\$$//' | sed -e 's/##//'

all:            ## Run an entire CI pipeline
	make format lint

##

install:        ## Install dependencies
	pdm install

update:         ## Update dependencies
	pdm update
	dipdup self update -q

format:         ## Format with all tools
	make black

lint:           ## Lint with all tools
	make ruff mypy

##

black:          ## Format with black
	black .

ruff:           ## Lint with ruff
	ruff check --fix .

mypy:           ## Lint with mypy
	mypy .

##

image:          ## Build Docker image
	docker buildx build . -t ${PACKAGE}:${TAG} --load

up:             ## Start Compose stack
	docker-compose -f ${COMPOSE} --env-file ${ENV_FILE} up -d --build
	docker-compose -f ${COMPOSE} --env-file ${ENV_FILE} logs -f

down:           ## Stop Compose stack
	docker-compose -f ${COMPOSE} --env-file ${ENV_FILE} down

prune:          ## Prune Docker resources
	make down
	docker volume rm ${PACKAGE}_db || true
##