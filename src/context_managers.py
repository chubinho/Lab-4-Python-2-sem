# src/context_managers.py
import asyncio
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


class AsyncDBConnection:
    """
    Асинхронный контекстный менеджер для имитации подключения к БД
    """

    def __init__(self, connection_string: str) -> None:
        self.connection_string = connection_string
        self.is_open: bool = False

    async def __aenter__(self) -> 'AsyncDBConnection':
        logger.info(f"Подключаюсь к БД: {self.connection_string}")
        await asyncio.sleep(0.1)
        self.is_open = True
        logger.info("Подключение установлено")
        return self

    async def __aexit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[Any]
    ) -> bool:
        if self.is_open:
            await asyncio.sleep(0.1)
            self.is_open = False
            logger.info("Подключение закрыто")

        if exc_type is not None:
            logger.warning(
                f"Ресурс закрыт, но произошло исключение: {exc_val}")
        return False

    async def execute(self, query: str) -> str:
        """Имитация выполнения запроса"""
        if not self.is_open:
            raise RuntimeError(
                "Сначала откройте соединение через `async with`")
        await asyncio.sleep(0.2)
        return f"Результат выполнения: {query}"
