import os
import psycopg2
from dotenv import load_dotenv

load_dotenv(encoding='utf-8')

def get_connection():
    """Возвращает подключение к PostgreSQL"""
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )