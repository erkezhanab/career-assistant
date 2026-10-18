import os
import subprocess
from datetime import datetime
# Если используете python-dotenv для настроек
# from dotenv import load_dotenv
# load_dotenv()

def run_pg_dump():
    # Эти данные должны совпадать с вашим DATABASE в settings.py
    DB_NAME = "career_assistant" # Из файла: Owner: postgres
    DB_USER = "postgres"
    
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    filename = f"backup_{timestamp}.sql"
    
    # Команда для выполнения дампа
    command = f"pg_dump -U {DB_USER} {DB_NAME} > {filename}"
    
    try:
        print(f"Creating SQL dump: {filename}...")
        subprocess.run(command, shell=True, check=True)
        print("Done!")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    run_pg_dump()