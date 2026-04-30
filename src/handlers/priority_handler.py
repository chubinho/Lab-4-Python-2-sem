import asyncio
import logging
from src.handler_protocol import TaskHandler
from src.task import Task

logger = logging.getLogger(__name__)


class HighPriorityHandler(TaskHandler):
    """Обрабатывает задачи с высоким приоритетом (>= 8)."""

    async def can_handle(self, task: Task) -> bool:
        return task.priority >= 8

    async def handle(self, task: Task) -> None:
        logger.info(f"Задача #{task.id} | Приоритет: {task.priority}")
        await asyncio.sleep(0.1) 
        logger.info(f"Задача #{task.id} выполнена")
