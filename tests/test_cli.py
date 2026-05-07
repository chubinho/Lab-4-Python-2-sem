import pytest
from typer.testing import CliRunner
from pathlib import Path
import json

from src.cli import app

runner = CliRunner()


class TestCLICommands:

    def test_cli_help_shows_commands(self):
        """Проверка, что --help показывает все команды"""
        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        assert "file" in result.stdout
        assert "generate" in result.stdout
        assert "api" in result.stdout
        assert "all" in result.stdout
        assert "process" in result.stdout  # Добавили проверку твоей команды process

    def test_generate_default_count(self):
        """Генерация задач с параметрами по умолчанию"""
        result = runner.invoke(app, ["generate"])
        assert result.exit_code == 0
        assert "5 задач" in result.stdout

    def test_generate_custom_count(self):
        """Генерация с кастомным количеством задач"""
        result = runner.invoke(app, ["generate", "--count", "30"])
        assert result.exit_code == 0
        assert "30 задач" in result.stdout

    def test_api_command(self):
        """Проверка команды api — задачи из заглушки."""
        result = runner.invoke(app, ["api"])
        assert result.exit_code == 0
        # В зависимости от того, сколько задач возвращает APIMockSource()
        # Если возвращает 3, проверка пройдет успешно
        assert "3 задач" in result.stdout

    def test_file_with_valid_json(self, tmp_path):
        """Загрузка задач из JSON-файла"""
        test_file = tmp_path / "tasks.json"

        # Передаем структуру, которую ожидает твой FileSource / Task дескрипторы
        data = [
            {"id": 1, "payload": {"description": "Test 1",
                                  "priority": 5, "status": "new"}},
            {"id": 2, "payload": {"description": "Test 2",
                                  "priority": 3, "status": "new"}},
        ]
        test_file.write_text(json.dumps(data))
        result = runner.invoke(app, ["file", str(test_file)])

        assert result.exit_code == 0
        assert "2 задач" in result.stdout

    def test_all_command_with_custom_file(self, tmp_path):
        """Команда all с кастомным файлом"""
        test_file = tmp_path / "tasks.json"
        data = [{"id": 1, "payload": {
            "description": "Test 1", "priority": 5, "status": "new"}}]
        test_file.write_text(json.dumps(data))

        result = runner.invoke(
            app, ["all", "--file", str(test_file), "--count", "2"])

        assert result.exit_code == 0
        assert "Успешно" in result.stdout

    def test_cli_error_handling(self):
        """Проверка обработки ошибок в CLI при невалидных аргументах"""
        result = runner.invoke(app, ["generate", "--count", "-1"])
        assert result.exit_code != 0

    def test_file_with_invalid_json(self, tmp_path):
        """Файл с невалидным JSON должен корректно обрабатываться"""
        test_file = tmp_path / "invalid.json"
        test_file.write_text('{ not valid json }')

        result = runner.invoke(app, ["file", str(test_file)])

        assert result.exit_code != 0
        assert any(word in result.stdout for word in [
                   "Ошибка", "error", "Invalid", "Error"])
