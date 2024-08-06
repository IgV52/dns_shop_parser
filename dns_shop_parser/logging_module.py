from asyncio import sleep
from logging.handlers import QueueHandler, QueueListener
from logging import StreamHandler, getLogger, INFO
from queue import Queue
from sys import stdout


async def init_logger():
    logger = getLogger("dns_shop_parser")
    queue = Queue()
    logger.addHandler(QueueHandler(queue))
    logger.setLevel(INFO)
    listener = QueueListener(queue, StreamHandler(stream=stdout))

    try:
        listener.start()
        while True:
            await sleep(60)
    finally:
        listener.stop()
