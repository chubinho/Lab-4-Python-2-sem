import pytest
import asyncio
import types
from src.task import Task
from src.task_queue import TaskQueue


@pytest.fixture
def sample_tasks():
    """Фикстура с набором задач для синхронных тестов."""
    return [
        Task(1, {"status": "new", "priority": 1, "description": "Task 1"}),
        Task(2, {"status": "done", "priority": 5, "description": "Task 2"}),
        Task(3, {"status": "new", "priority": 3, "description": "Task 3"})
    ]


def test_queue_length(sample_tasks):
    queue = TaskQueue(sample_tasks)
    assert len(queue) == 3


def test_iteration_protocol():
    task = Task(1, {"status": "new", "priority": 1, "description": "Test"})
    queue = TaskQueue([task])
    it = iter(queue)
    assert next(it).id == 1
    with pytest.raises(StopIteration):
        next(it)


def test_repeatable_iteration(sample_tasks):
    queue = TaskQueue(sample_tasks)
    first = list(queue)
    second = list(queue)
    assert len(first) == len(second) == 3
    assert [t.id for t in first] == [t.id for t in second]


def test_lazy_filter_status(sample_tasks):
    queue = TaskQueue(sample_tasks)
    new_tasks = list(queue.filter_by_status("new"))
    assert len(new_tasks) == 2
    assert all(t.status == "new" for t in new_tasks)


def test_lazy_filter_priority(sample_tasks):
    queue = TaskQueue(sample_tasks)
    high_priority = list(queue.filter_by_priority(3))
    assert len(high_priority) == 2
    assert all(t.priority >= 3 for t in high_priority)


def test_generator_is_lazy(sample_tasks):
    queue = TaskQueue(sample_tasks)
    gen = queue.filter_by_status("new")
    assert isinstance(gen, types.GeneratorType)


def test_empty_queue_iteration():
    queue = TaskQueue()
    assert list(queue) == []
    assert len(queue) == 0


@pytest.mark.asyncio
async def test_async_put_and_get():
    queue = TaskQueue()
    task = Task(1, {"status": "new", "priority": 1,
                "description": "Async Test"})
    await queue.put(task)
    assert len(queue) == 1

    retrieved = await queue.get()
    assert retrieved.id == 1
    queue.task_done()


@pytest.mark.asyncio
async def test_fifo_ordering():
    queue = TaskQueue()
    for i in range(1, 4):
        await queue.put(Task(i, {"status": "new", "priority": i, "description": f"Task {i}"}))

    ids = []
    for _ in range(3):
        t = await queue.get()
        ids.append(t.id)
        queue.task_done()
    assert ids == [1, 2, 3]


@pytest.mark.asyncio
async def test_join_waits_for_completion():
    queue = TaskQueue()
    processed = []

    async def worker():
        while True:
            task = await queue.get()
            await asyncio.sleep(0.01)  # имитация работы
            processed.append(task.id)
            queue.task_done()

    worker_task = asyncio.create_task(worker())
    for i in range(1, 4):
        await queue.put(Task(i, {"status": "new", "priority": 5, "description": f"Task {i}"}))

    await queue.join()
    worker_task.cancel()
    try:
        await worker_task
    except asyncio.CancelledError:
        pass

    assert sorted(processed) == [1, 2, 3]


@pytest.mark.asyncio
async def test_non_blocking_concurrent_put():
    queue = TaskQueue()
    results = []

    async def producer():
        for i in range(1, 4):
            await queue.put(Task(i, {"status": "new", "priority": i, "description": f"Task {i}"}))
            results.append(f"put_{i}")
            await asyncio.sleep(0)  # явная передача управления event loop

    async def consumer():
        for _ in range(3):
            task = await queue.get()
            results.append(f"get_{task.id}")
            queue.task_done()

    await asyncio.gather(producer(), consumer())
    assert "put_1" in results and "get_1" in results
