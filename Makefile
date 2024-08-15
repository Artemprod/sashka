run_worker:
	poetry run python /app/src/consumption/fast_streem_app_run.py

run_server:
	poetry run python /app/src/api/app/server_app_run.py

run_redis:
	redis-server --port ${REDIS_PORT}

make-migrations:
	alembic revision --autogenerate

migrate:
	alembic upgrade head
#
#.PHONY: help
#
#help: # Run `make help` to get help on the make commands
#	@grep -E '^[0-9a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
