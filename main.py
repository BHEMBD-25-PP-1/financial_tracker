from fastapi import FastAPI

from app.analytics.controllers import router as analytics_router
from app.auth.controllers import router as auth_router
from app.groups.controllers import router as groups_router
from app.transactions.controllers import router as transactions_router

app = FastAPI(
    title="Finance Tracker API",
    version="1.0.0",
    description="API для управления транзакциями",
)

# Подключение версионированного API
app.include_router(auth_router, prefix="/api/v1")
app.include_router(transactions_router, prefix="/api/v1")
app.include_router(groups_router, prefix="/api/v1")
app.include_router(analytics_router, prefix="/api/v1")


@app.get("/")
def read_root():
    """Корневой эндпоинт."""
    return {"message": "Finance Tracker API", "version": "1.0.0"}