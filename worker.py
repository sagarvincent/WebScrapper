"""RQ worker entry point.

Run one or more of these alongside the web tier:

    python worker.py

Each worker connects to Redis, ensures the Postgres schema exists, and then
blocks pulling scrape jobs off the queue and running them.
"""

from rq import Worker

from src import db
from webapp.jobs import QUEUE_NAME, get_queue


def main():
    db.init_schema()
    queue = get_queue()
    worker = Worker([queue], connection=queue.connection)
    worker.work(with_scheduler=False)


if __name__ == "__main__":
    main()
