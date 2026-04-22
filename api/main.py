"""
Главная точка входа FastAPI-приложения.

Создаёт экземпляр FastAPI и подключает роуты по отдельным метрикам.
"""

from fastapi import FastAPI

from src.metrics.m2_api import router as m2_router
from src.metrics.m2_broad_api import router as m2_broad_router
from src.metrics.exchange_rate_api import router as exchange_rate_router
from src.metrics.avg_exchange_rate_api import router as avg_exchange_rate_router


def create_app() -> FastAPI:
    """Создает экземпляр FastAPI-приложения."""
    app = FastAPI(
        title="Fin Web App API",
        description="API для работы с показателями ЦБ РФ.",
        version="0.1.0",
    )

    # Подключение роутеров из src\metrics\
    app.include_router(m2_router)
    app.include_router(m2_broad_router)
    app.include_router(exchange_rate_router)
    app.include_router(avg_exchange_rate_router)

    @app.get("/")
    def root():
        """Проверка работоспособности сервера"""
        return {"status": "ok", "message": "Fin Web App API is running"}

    return app

app = create_app()