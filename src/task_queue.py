import asyncio
from typing import Iterator, Optional, List
from src.task import Task


class TaskQueue:
    """Коллекция для хранения, ленивой фильтрации и асинхронной обработки задач"""

    def __init__(self, tasks: Optional[List[Task]] = None) -> None:
        self._tasks: List[Task] = list(tasks) if tasks else []
        self._queue: asyncio.Queue[Task] = asyncio.Queue()

        for task in self._tasks:
            self._queue.put_nowait(task)

    async def put(self, task: Task) -> None:
        self._tasks.append(task)
        await self._queue.put(task)

    async def get(self) -> Task:
        return await self._queue.get()

    def task_done(self) -> None:
        self._queue.task_done()

    async def join(self) -> None:
        await self._queue.join()

    def __len__(self) -> int:
        return len(self._tasks)

    def __iter__(self) -> 'TaskQueueIterator':
        return TaskQueueIterator(self._tasks)

    def filter_by_status(self, status: str) -> Iterator[Task]:
        """Ленивая фильтрация по статусу."""
        for task in self._tasks:
            if task.status == status:
                yield task

    def filter_by_priority(self, min_priority: int) -> Iterator[Task]:
        """Ленивая фильтрация по приоритету."""
        for task in self._tasks:
            if task.priority >= min_priority:
                yield task


class TaskQueueIterator:
    """Итератор для обхода задач"""

    def __init__(self, tasks: List[Task]) -> None:
        self._tasks = tasks
        self._cursor = 0

    def __next__(self) -> Task:
        if self._cursor >= len(self._tasks):
            raise StopIteration
        task = self._tasks[self._cursor]
        self._cursor += 1
        return task

    def __iter__(self) -> 'TaskQueueIterator':
        return self
