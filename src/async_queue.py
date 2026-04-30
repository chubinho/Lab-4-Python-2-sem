import asyncio
import logging
from src.task import Task
from typing import Optional 

logger = logging.getLogger(__name__)

class AsyncTaskQueue:
    """Асинхронная очередь для обработки задач"""

    def __init__(self, maxsize: int = 0) -> None:
        self._queue: asyncio.Queue[Task] = asyncio.Queue(maxsize=maxsize)

    async def put(self,  task: Task) -> None:
        await self._queue.put(task)
        logger.debug(f"Задача {task} добавлена в очередь")

    async def get(self) -> Task:
        task = await self._queue.get()
        logger.debug(f"Задача {task} извлечена из очереди")
        return task

    def task_done(self) -> None:
        self._queue.task_done()
    
    async def join(self) -> None:
        await self._queue.join()
    
    @property
    def size(self) -> int:
        return self._queue.qsize()