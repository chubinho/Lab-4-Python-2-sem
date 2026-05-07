import asyncio
import logging

from src.async_queue import AsyncTaskQueue
from src.handler_protocol import TaskHandler
from src.task import Task

logger = logging.getLogger(__name__)


class TaskWorker:
    """Асинхронный воркер: координирует пул параллельных обработчиков задач"""

    def __init__(self, queue: AsyncTaskQueue, handlers: list[TaskHandler], max_workers: int = 5) -> None:
        self.queue = queue
        self.handlers = handlers
        self.max_workers = max_workers 
        self._worker_tasks: list[asyncio.Task] = []

    async def _route_task(self, task: Task) -> None:
        for handler in self.handlers:
            if await handler.can_handle(task):
                await handler.handle(task)
                return
        logger.warning(f"Нет подходящего обработчика для задачи #{task.id}")

    async def _worker_loop(self, worker_id: int) -> None:
        """Индивичил одного воркера в пуле"""
        logger.debug(f"Воркер {worker_id} запущен")
        try:
            while True:
                task = await self.queue.get()
                try:
                    await self._route_task(task)
                except Exception as e:
                    logger.error(
                        f"Ошибка обработки задачи #{task.id} воркером {worker_id}: {e}", exc_info=True)
                finally:
                    self.queue.task_done()
        except asyncio.CancelledError:
            logger.debug(f"Воркер {worker_id} завершает работу")
            raise

    async def start(self) -> None:
        """Запуск пула параллельных воркеров"""
        logger.info(f"Запуск {self.max_workers} асинхронных воркеров...")
        self._worker_tasks = [
            asyncio.create_task(self._worker_loop(i)) for i in range(self.max_workers)
        ]

    async def stop(self) -> None:
        """Graceful shutdown: ожидание завершения очереди и отмена воркеров"""
        logger.info("Ожидание завершения всех задач in очереди...")
        await self.queue.join() 

        logger.info("Остановка воркеров...")
        for task in self._worker_tasks:
            task.cancel()

        await asyncio.gather(*self._worker_tasks, return_exceptions=True)
        logger.info("Все воркеры успешно остановлены")
