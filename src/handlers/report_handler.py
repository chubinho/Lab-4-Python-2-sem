# src/handlers/report_handler.py
import asyncio
import logging
from src.handler_protocol import TaskHandler
from src.task import Task
from src.context_managers import AsyncDBConnection

logger = logging.getLogger(__name__)


class ReportHandler(TaskHandler):
    """Генерирует отчёт и сохраняет его в БД через async context manager"""

    async def can_handle(self, task: Task) -> bool:
        return task.payload.get("type") == "report"

    async def handle(self, task: Task) -> None:
        report_name = task.payload.get("report_name", "default_report")

        async with AsyncDBConnection("postgres://localhost:5432/tasks_db") as db:
            logger.info(f"Генерирую отчёт: {report_name}")
            await asyncio.sleep(0.3)

            query = f"INSERT INTO reports (task_id, name) VALUES ({task.id}, '{report_name}')"
            result = await db.execute(query)
            logger.info(f"Сохранено в БД: {result}")
