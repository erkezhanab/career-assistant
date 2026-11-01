"""
Скрипт резервного копирования базы данных.

Запуск: python db_backup.py

Создаёт SQL-дамп базы через стандартную утилиту PostgreSQL pg_dump.
Имя файла содержит дату и время, поэтому прошлые копии не затираются.
Файлы backup*.sql исключены из репозитория (см. .gitignore).
"""

import os
import subprocess
from datetime import datetime
# Если используете python-dotenv для настроек
# from dotenv import load_dotenv
# load_dotenv()


def run_pg_dump():
    """Выполняет резервное копирование базы в файл."""
    # Эти данные должны совпадать с вашим DATABASE в settings.py
    DB_NAME = "career_assistant"
    DB_USER = "postgres"

    # Метка времени в имени файла: backup_2026-11-01_12-30-00.sql
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    filename = f"backup_{timestamp}.sql"

    # Команда для выполнения дампа
    # Знак > перенаправляет вывод pg_dump в файл
    command = f"pg_dump -U {DB_USER} {DB_NAME} > {filename}"

    try:
        print(f"Creating SQL dump: {filename}...")
        # shell=True нужен для работы перенаправления «>».
        # check=True поднимает исключение, если pg_dump завершился с ошибкой
        subprocess.run(command, shell=True, check=True)
        print("Done!")
    except Exception as e:
        # Частые причины: не запущен PostgreSQL или нет прав у пользователя
        print(f"Error: {e}")


# Этот блок выполняется только при прямом запуске файла,
# но не при импорте его из другого модуля
if __name__ == "__main__":
    run_pg_dump()
