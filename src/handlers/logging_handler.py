import logging
from src.handler_protocol import TaskHandler
from src.task import Task

logger = logging.getLogger(__name__)


class LoggingHandler(TaskHandler):
    """Fallback-обработчик: логирует всё, что не подошло другим"""

    async def can_handle(self, task: Task) -> bool:
        return True

    async def handle(self, task: Task) -> None:
        logger.info(
            f"Задача #{task.id} | Статус: {task.status} | Payload: {task.payload}")
