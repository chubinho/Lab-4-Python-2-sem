import asyncio
import logging
from src.handler_protocol import TaskHandler
from src.task import Task

logger = logging.getLogger(__name__)


class ApiHandler(TaskHandler):
    """Имитируеv асинхронный HTTP-запрос к внешнему API"""

    async def can_handle(self, task: Task) -> bool:
        return task.status == "api_call" or task.payload.get("type") == "api"

    async def handle(self, task: Task) -> None:
        logger.info(f"Отправляю запрос для задачи #{task.id}")
        await asyncio.sleep(0.5)
        logger.info(f"Ответ 200 OK для задачи #{task.id}")
