import logging
import os
from redis import Redis
from rq import Connection, Worker

from app.core.config import settings


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    redis_conn = Redis.from_url(settings.redis_url)
    with Connection(redis_conn):
        worker = Worker([settings.rq_queue])
        worker.work(with_scheduler=False)