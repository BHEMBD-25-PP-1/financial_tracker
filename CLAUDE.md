# Project: Financial tracker - приложение для отслеживания расходов

## Project Description
Приложение для управления личными финансами, позволяющее пользователям фиксировать доходы и расходы и получать аналитику по ним.

## Tech Stack
- **Backend**:** FastAPI + Python
- **Database**: PostgreSQL 
- **ORM**: SQLAlchemy 
- **Migrations**: Alembic 
- **Containerization**: Docker Compose 
- **Authentication**: JWT

## Code Conventions
- **Python**: PEP 8 рекомендации
- **Naming**: snake_case для переменных/методов, PascalCase для классов
- **Type Hints**: Обязательны для всех функций и методов
- **Imports**: Групповой (стандартная библиотека, сторонний, локальный) с помощью isort

## Development Approaches

### Current Architecture Implementation
- **API-First Development**: Сначала спецификации OpenAPI, затем код. Генерация кода из специификации
- **Module-Based Structure**: Четкое разделение по функциональным модулям:
app/
├── auth/          # Аутентификация и авторизация
├── transactions/  # Управление транзакциями  
├── groups/        # Группы пользователей
└── analytics/     # Аналитика и отчеты
- **FastAPI Dependency Injection**: Используется для аутентификации (в планах)
async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:

### Current Testing Strategy
- **API Contract Testing**: Тестирование по OpenAPI спецификациям
- **Error Handling Pattern**: Единый формат ошибок. Все контроллеры используют модель Error

### Database Layer Approach
- **SQLAlchemy ORM**: Декларативные модели для БД
- **Alembic Migrations**: Управление версиями схемы БД

### API Design Patterns
- **RESTful Resource Naming**
- **Standard Response Formats**
- **Query Parameter Standards**
- **Единые параметры для фильтрации**

## API

### Аутентификация (/api/v1/auth)
- POST /auth/register - Регистрация пользователя
- POST /auth/login - Авторизация (JWT)
- POST /auth/refresh - Обновление токенов
- POST /auth/change-password - Смена пароля
- GET /auth/me - Информация о текущем пользователе

### Транзакции (/api/v1/transactions)
- GET /transactions - Список транзакций с фильтрами
- POST /transactions - Создание транзакции
- GET /transactions/{id} - Получение транзакции по ID
- PUT /transactions/{id} - Обновление транзакции
- DELETE /transactions/{id} - Удаление транзакции

### Группы (/api/v1/groups)
- GET /groups - Список групп пользователя
- POST /groups - Создание группы
- GET /groups/{id} - Получение группы по ID
- PUT /groups/{id} - Обновление группы
- DELETE /groups/{id} - Удаление группы
- GET /groups/{id}/members - Участники группы
- POST /groups/{id}/members - Добавление участника
- DELETE /groups/{id}/members/{user_id} - Удаление участника
- GET /groups/{id}/analytics - Аналитика по группе

### Аналитика (/api/v1/analytics)
- GET /analytics/summary - Общая статистика
- GET /analytics/by-category - Статистика по категориям
- GET /analytics/by-period - Статистика по периодам
- GET /analytics/trends - Тренды доходов/расходов

## Data model

### Пользователь (User)
- id, first_name, last_name, login, password_hash
- created_at, updated_at

### Транзакция (Transaction)
- id, name, type (income/expense), category, amount, date
- user_id, group_id (опционально)
- created_at, updated_at

### Группа (Group)
- id, name, owner_id
- created_at, updated_at

### Участник группы (UserGroup)
- id, user_id, group_id, role (owner/member)
- joined_at

