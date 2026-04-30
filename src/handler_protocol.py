from typing import Protocol, runtime_checkable
from src.task import Task


@runtime_checkable
class TaskHandler(Protocol):
    # Контракт для асинхронных обработчиков задач

    async def can_handle(self, task: Task):
        """Проверяет, может ли обработчик взять эту задачу"""
        ...

    async def handle(self, task: Task):
        """Выполняет асинхронную обработку задачи"""
        ...
