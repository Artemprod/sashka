# import pytz
# from apscheduler.jobstores.redis import RedisJobStore
# from apscheduler.schedulers.asyncio import AsyncIOScheduler
# from loguru import logger
#
# from configs.redis import redis_apscheduler_config
#
#
# class ApschedulerManager:
#     def __init__(self):
#         """Инициализирует планировщик для планирования задач."""
#
#         jobstores = {
#             "default": RedisJobStore(
#                 jobs_key=redis_apscheduler_config.jobs_key,  # Ключ для хранения заданий
#                 run_times_key=redis_apscheduler_config.run_times_key,  # Ключ для времени выполнения
#                 host=redis_apscheduler_config.host,
#                 port=redis_apscheduler_config.port,
#                 db=redis_apscheduler_config.research_start_database,
#             )
#         }
#
#         scheduler = AsyncIOScheduler(jobstores=jobstores, timezone=pytz.utc)
#         scheduler.start()
#         self._scheduler = scheduler
#
#     def get_scheduler(self) -> AsyncIOScheduler:
#         return self._scheduler
#
#     def delete_scheduled_task(
#             self,
#             prefix: str
#     ) -> int:
#         """
#         Removes scheduled tasks based on the job id prefix.
#
#         :param prefix: Prefix to identify the task.
#         :return: Number of removed jobs.
#         """
#         removed_jobs_count = 0
#         for job in self._scheduler.get_jobs():
#             if job.id.startswith(prefix):
#                 logger.info(f"Job ID: {job.id}")
#                 self._scheduler.remove_job(job.id)
#                 logger.info(f"Removed job: {job.id}")
#                 removed_jobs_count += 1
#         return removed_jobs_count
#
# scheduler_manager = ApschedulerManager()
