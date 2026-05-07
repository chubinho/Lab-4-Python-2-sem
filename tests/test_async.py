import asyncio
import pytest
from src.async_queue import AsyncTaskQueue
from src.worker import TaskWorker
from src.task import Task
from src.context_managers import AsyncDBConnection

# =====================================================================
# ФЕЙКОВЫЕ ХЭНДЛЕРЫ ДЛЯ ТЕСТИРОВАНИЯ (MOCKS)
# =====================================================================


class BrokenHandler:
    """Хэндлер, который всегда падает с ошибкой для проверки отказоустойчивости"""

    async def can_handle(self, task: Task) -> bool:
        return True

    async def handle(self, task: Task) -> None:
        raise RuntimeError("Критический сбой хэндлера!")


class FirstHandler:
    """Хэндлер, который пропускает задачу дальше по цепочке"""

    def __init__(self):
        self.called = False

    async def can_handle(self, task: Task) -> bool:
        return False

    async def handle(self, task: Task) -> None:
        self.called = True


class SecondHandler:
    """Хэндлер, который перехватывает задачу"""

    def __init__(self):
        self.called = False

    async def can_handle(self, task: Task) -> bool:
        return True

    async def handle(self, task: Task) -> None:
        self.called = True



@pytest.mark.asyncio
async def test_queue_put_and_get():
    """Базовая проверка асинхронного добавления и извлечения из очереди"""
    queue = AsyncTaskQueue()
    task = Task(id=1, payload={"test": True})

 
    await queue.put(task)
    assert queue.size == 1

    extracted_task = await queue.get()
    assert extracted_task.id == 1
    assert queue.size == 0


@pytest.mark.asyncio
async def test_queue_maxsize_blocking():
    """Проверка блокировки очереди при достижении maxsize"""
    queue = AsyncTaskQueue(maxsize=1)
    task1 = Task(id=1, payload={"test": 1})
    task2 = Task(id=2, payload={"test": 2})

    await queue.put(task1)
    assert queue.size == 1

    put_task = asyncio.create_task(queue.put(task2))

    await asyncio.sleep(0.05)
    assert queue.size == 1
    assert not put_task.done()

    await queue.get()

    await put_task
    assert queue.size == 1


@pytest.mark.asyncio
async def test_worker_survives_handler_error():
    """Проверка изоляции ошибок (воркер не умирает, если хэндлер упал)"""
    queue = AsyncTaskQueue()
    worker = TaskWorker(queue, handlers=[BrokenHandler()], max_workers=1)

    task1 = Task(id=1, payload={"data": "broken"})
    task2 = Task(id=2, payload={"data": "next"})

    await queue.put(task1)
    await queue.put(task2)

    await worker.start()
    await queue.join() 
    await worker.stop()

    assert queue.size == 0




@pytest.mark.asyncio
async def test_db_connection_context_manager():
    """Проверка асинхронного контекстного менеджера БД (включая работу при ошибках)"""
    db = AsyncDBConnection("localhost:5432")
    assert db.is_open is False

    async with db as conn:
        assert conn.is_open is True
        result = await conn.execute("SELECT 1")
        assert "Результат выполнения" in result
    assert db.is_open is False


    try:
        async with db as conn:
            assert conn.is_open is True
            raise ValueError("Сбой логики")
    except ValueError:
        pass  

    assert db.is_open is False


@pytest.mark.asyncio
async def test_worker_graceful_shutdown():
    """Проверка Graceful Shutdown (все воркеры останавливаются корректно)"""
    queue = AsyncTaskQueue()
    worker = TaskWorker(queue, handlers=[], max_workers=3)

    await worker.start()

    assert len(worker._worker_tasks) == 3
    for task in worker._worker_tasks:
        assert not task.done()

    await worker.stop()

    for task in worker._worker_tasks:
        assert task.done()
