import asyncio
import logging
from pathlib import Path
from typing import Optional

import typer
import sys
from src.async_queue import AsyncTaskQueue
from src.worker import TaskWorker
from src.handlers.api_handler import ApiHandler
from src.handlers.report_handler import ReportHandler
from src.handlers.logging_handler import LoggingHandler
from src.handlers.priority_handler import HighPriorityHandler
from src.sources.file_source import FileSource
from src.sources.generator_source import GeneratorConfig, GeneratorSource
from src.sources.api_mock_source import APIMockSource
from src.consumer import TaskConsumer
from src.logger import set_logger

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

app = typer.Typer(help="Асинхронная платформа обработки задач")


async def run_processor(tasks_to_load):
    queue = AsyncTaskQueue()
    handlers = [
        HighPriorityHandler(),
        ReportHandler(),
        ApiHandler(),
        LoggingHandler()
    ]
    worker = TaskWorker(queue, handlers)

    for t in tasks_to_load:
        await queue.put(t)

    typer.echo(f"Загружено в асинхронную очередь: {len(tasks_to_load)} задач")

    await worker.start()
    await worker.stop()

    typer.echo("Обработка всех задач завершена. Успешно")


@app.command(help="Запуск обработки. Флаги: [-n count, --status, --priority]")
def process(
    count: int = typer.Option(10, "--count", "-n"),
    status: Optional[str] = typer.Option(None, "--status"),
    priority: Optional[int] = typer.Option(None, "--priority")
):
    consumer = TaskConsumer()
    source = GeneratorSource(GeneratorConfig(count=count))
    tasks = consumer.accept_tasks(source)

    if status:
        tasks = [t for t in tasks if t.status == status]
    if priority:
        tasks = [t for t in tasks if t.priority >= priority]

    asyncio.run(run_processor(tasks))


@app.command(help="Загрузка из JSON. Аргументы: [PATH]")
def file(path: Path = typer.Argument(...)):
    consumer = TaskConsumer()
    try:
        source = FileSource(path)
        tasks = consumer.accept_tasks(source)
        asyncio.run(run_processor(tasks))
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        typer.echo(f"Ошибка: {e}")
        raise typer.Exit(1)


@app.command(help="Генерация тестовых задач. Флаги: [-n count]")
def generate(
    count: int = typer.Option(5, "--count", "-n"),
    prefix: str = typer.Option("task_", "--prefix", "-p")
):
    consumer = TaskConsumer()
    try:
        config = GeneratorConfig(count=count, prefix=prefix)
        source = GeneratorSource(config)
        tasks = consumer.accept_tasks(source)
        asyncio.run(run_processor(tasks))
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        typer.echo(f"Ошибка: {e}")
        raise typer.Exit(1)


@app.command(help="Получение задач из API-заглушки")
def api():
    consumer = TaskConsumer()
    try:
        source = APIMockSource()
        tasks = consumer.accept_tasks(source)
        asyncio.run(run_processor(tasks))
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        typer.echo(f"Ошибка: {e}")
        raise typer.Exit(1)


@app.command(help="Запуск из всех источников. Флаги: [-f file, -n count]")
def all(
    file_path: Path = typer.Option("messages.json", "--file", "-f"),
    count: int = typer.Option(3, "--count", "-n")
):
    consumer = TaskConsumer()
    try:
        sources = [
            FileSource(file_path),
            GeneratorSource(GeneratorConfig(count=count)),
            APIMockSource(),
        ]
        tasks = consumer.accept_tasks_from_multiple_sources(sources)
        asyncio.run(run_processor(tasks))
    except Exception as e:
        logger.exception(f"Ошибка: {e}")
        typer.echo(f"Ошибка: {e}")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
