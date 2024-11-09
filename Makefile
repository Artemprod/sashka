run_main_api:
	poetry run python /app/src/web/main.py

run_researcher:
	poetry run python /app/src/subscriber/resercher/run.py
run_communicator:
	poetry run python /app/src/subscriber/communicator/run.py

run_distributor:
	poetry run python /app/src/distributor/run.py
#run_redis:
#	redis-server --port ${REDIS_PORT}
#
#make-migrations:
#	alembic revision --autogenerate
#
#migrate:
#	alembic upgrade head
#
#.PHONY: help
#
#help: # Run `make help` to get help on the make commands
#	@grep -E '^[0-9a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
