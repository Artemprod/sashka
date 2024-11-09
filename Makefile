run_main_api:
	poetry run python /app/src/web/main.py

run_researcher:
	poetry run python /app/src/subscriber/resercher/run.py
run_communicator:
	poetry run python /app/src/subscriber/communicator/run.py

run_distributor:
	poetry run python /app/src/distributor/run.py

run_redis:
	redis-server --port ${REDIS_PORT}