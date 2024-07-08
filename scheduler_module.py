# -*- coding: utf-8 -*-
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.base import JobLookupError
from apscheduler.triggers.interval import IntervalTrigger
from logger_module import LoggerConfig
import inspect
import os

class Scheduler:
    def __init__(self):
        self.name = __name__
        self.scheduler = BackgroundScheduler()
        self.jobs = {}
        self.logger = LoggerConfig.get_logger('scheduler')

        frame = inspect.currentframe()
        caller_frame = frame.f_back
        self.caller_info = inspect.getframeinfo(caller_frame)

        self.scheduler.start()

    def add_job_condition(self, job_id, func, trigger, condition_func, *args, **kwargs):
        if job_id in self.jobs:
            self.logger.info(f"Job {job_id} is already running.")
            return
        job = self.scheduler.add_job(
            self._conditional_wrapper(func, condition_func),
            trigger,
            args=args,
            kwargs=kwargs,
            id=job_id
        )
        self.jobs[job_id] = job
        self.logger.info(f"Job {job_id} added.")

    def add_interval_job(self, func, seconds, job_id, **kwargs):
        """
        インターバルでジョブを追加
        :param func: 実行する関数
        :param seconds: ジョブの実行間隔（秒）
        :param job_id: ジョブのID
        :param kwargs: 関数に渡す追加の引数
        """
        if job_id in self.jobs:
            self.logger.info(f"Job {job_id} is already running.")
            return
        job = self.scheduler.add_job(func, 'interval', seconds=seconds, id=job_id, **kwargs)
        self.jobs[job_id] = job
        self.logger.info(f"Job {job_id} added to run every {seconds} seconds")

    def add_interval_job_condition(self, func, condition_func, seconds, job_id, **kwargs):
        """
        インターバルでジョブを追加、条件で実行
        :param func: 実行する関数
        :param condition_func: 条件関数
        :param seconds: ジョブの実行間隔（秒）
        :param job_id: ジョブのID
        :param kwargs: 関数に渡す追加の引数
        """
        if job_id in self.jobs:
            self.logger.info(f"Job {job_id} is already running.")
            return
        job = self.scheduler.add_job(
            self._conditional_wrapper(func, condition_func),
            'interval',
            seconds=seconds,
            id=job_id,
            **kwargs
            )
        self.jobs[job_id] = job
        self.logger.info(f"Job {job_id} added to run every {seconds} seconds")

    def add_cron_job(self, func, job_id, **cron_args):
        """
        Cron形式でジョブを追加
        :param func: 実行する関数
        :param job_id: ジョブのID
        :param cron_args: cronの引数（例：minute=0, hour=0で毎日深夜0時に実行）
        """
        if job_id in self.jobs:
            self.logger.info(f"Job {job_id} is already running.")
            return
            job = self.scheduler.add_job(func, 'cron', id=job_id, **cron_args)
            self.jobs[job_id] = job
            self.logger.info(f"Job {job_id} added with cron args: {cron_args}")

    def add_cron_job_condition(self, func, condition_func, job_id, **cron_args):
        """
        Cron形式でジョブを追加、条件で実行
        :param func: 実行する関
        :param condition_func: 条件関数
        :param job_id: ジョブのID
        :param cron_args: cronの引数（例：minute=0, hour=0で毎日深夜0時に実行）
        """
        if job_id in self.jobs:
            self.logger.info(f"Job {job_id} is already running.")
            return
        job = self.scheduler.add_job(
            self._conditional_wrapper(func, condition_func),
            'cron',
            id=job_id,
             **cron_args
         )
        self.jobs[job_id] = job
        self.logger.info(f"Job {job_id} added with cron args: {cron_args}")

    def modify_job(self, job_id, **changes):
        """Modify an existing job.

        Args:
            job_id (str): Unique identifier for the job.
            **changes: Parameters to modify the job.
        """
        try:
            self.scheduler.modify_job(job_id, **changes)
            self.logger.info(f"Modified job {job_id}")
        except JobLookupError:
            self.logger.info(f"Job {job_id} not found")

    def remove_job(self, job_id):
        """
        ジョブを削除
        :param job_id: 削除するジョブのID
        """
        if job_id in self.jobs:
            try:
                self.scheduler.remove_job(job_id)
                del self.jobs[job_id]
                self.logger.info(f"Job {job_id} removed")
            except JobLookupError:
                self.logger.info(f"Job {job_id} not found")
        else:
            self.logger.info(f"Job {job_id} is not running. Nothing to remove.")

    def _conditional_wrapper(self, func, condition_func):
        def wrapper(*args, **kwargs):
            if condition_func():
                self.logger.info(f"Condition met, executing job: {func.__name__}")
                func(*args, **kwargs)
            else:
                self.logger.info(f"Condition not met, skipping job: {func.__name__}")
        return wrapper

    def shutdown(self):
        """
        スケジューラをシャットダウン
        """
        self.logger.info(f'scheduler is shutting down from {os.path.basename(self.caller_info.filename)}')
        self.scheduler.shutdown()
        # print("Scheduler shutdown")

    def __del__(self):
        self.shutdown()

# 使用例
if __name__ == "__main__":
    import time

    def example_task():
        print("Executing task at", time.strftime("%Y-%m-%d %H:%M:%S"))

    scheduler = Scheduler()
    scheduler.add_interval_job(example_task, 10, 'example_job')

    try:
        while True:
            scheduler.add_job(
                job_id="test_job",
                func=test_job,
                trigger=IntervalTrigger(seconds=5),
                condition_func=sample_condition,
                message="Hello, world!"
            )

    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
