"""
Модуль подключения к PostgreSQL.

Содержит функцию для создания нового подключения к базе данных
на основе переменных окружения из файла .env.
"""

import os
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_PATH = BASE_DIR / ".env"

if ENV_PATH.exists():
    load_dotenv(ENV_PATH, encoding="utf-8")
else:
    print(f">>> WARNING: .env not found at {ENV_PATH}")

def get_connection():
    """Возвращает подключение к PostgreSQL"""
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )