import asyncio
import logging


from src.async_queue import AsyncTaskQueue
from src.handler_protocol import TaskHandler
from src.task import Task

logger = logging.getLogger(__name__)


class TaskWorker:
    """Асинхронный воркер: забирает задачи из очереди и маршрутизирует их к обработчикам"""

    def __init__(self, queue: AsyncTaskQueue, handlers: list[TaskHandler]) -> None:
        self.queue = queue
        self.handlers = handlers

    async def _route_task(self, task: Task) -> None:
        """Находит первый подходящий обработчик и выполняет задачу"""
        for handler in self.handlers:
            if await handler.can_handle(task):
                await handler.handle(task)
                return
        logger.warning(f"Нет подходящего обработчика для задачи #{task.id}")

    async def run(self) -> None:
        """Основной цикл воркера"""
        logger.info("Воркер запущен")
        try:
            while True:
                task = await self.queue.get()
                try:
                    await self._route_task(task)
                except Exception as e:
                    logger.error(
                        f"Ошибка обработки задачи #{task.id}: {e}", exc_info=True)
                finally:
                    self.queue.task_done()
        except asyncio.CancelledError:
            logger.info("Воркер корректно остановлен")