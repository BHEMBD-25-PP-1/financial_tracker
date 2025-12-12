"""add_test_data

Revision ID: 3b9fa3bda428
Revises: 5b9f6b27fe45
Create Date: 2025-12-10 17:42:34.977043

"""
from typing import Sequence, Union
from datetime import datetime, date

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3b9fa3bda428'
down_revision: Union[str, None] = '5b9f6b27fe45'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Добавить тестовые данные в базу."""
    connection = op.get_bind()
    now = datetime.utcnow()
    
    # Хеш пароля для тестовых пользователей (пароль: "password123")
    # Используем готовый bcrypt хеш для избежания проблем с зависимостями в миграции
    # Хеш создан через bcrypt для пароля "password123" с rounds=12
    # Формат: $2b$12$[salt][hash] (60 символов)
    password_hash = "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW"
    
    # Создание тестовых пользователей
    users_table = sa.table(
        'users',
        sa.column('id', sa.Integer),
        sa.column('first_name', sa.String),
        sa.column('last_name', sa.String),
        sa.column('login', sa.String),
        sa.column('password_hash', sa.String),
        sa.column('created_at', sa.DateTime),
        sa.column('updated_at', sa.DateTime),
    )
    
    connection.execute(
        users_table.insert().values([
            {
                'first_name': 'Иван',
                'last_name': 'Иванов',
                'login': 'ivanov',
                'password_hash': password_hash,
                'created_at': now,
                'updated_at': now,
            },
            {
                'first_name': 'Мария',
                'last_name': 'Петрова',
                'login': 'petrova',
                'password_hash': password_hash,
                'created_at': now,
                'updated_at': now,
            },
            {
                'first_name': 'Алексей',
                'last_name': 'Сидоров',
                'login': 'sidorov',
                'password_hash': password_hash,
                'created_at': now,
                'updated_at': now,
            },
            {
                'first_name': 'Елена',
                'last_name': 'Козлова',
                'login': 'kozlova',
                'password_hash': password_hash,
                'created_at': now,
                'updated_at': now,
            },
        ])
    )
    
    # Получаем ID созданных пользователей
    result = connection.execute(
        sa.text("SELECT id, login FROM users WHERE login IN ('ivanov', 'petrova', 'sidorov', 'kozlova') ORDER BY login")
    )
    user_ids = {row[1]: row[0] for row in result}
    
    # Создание групп
    groups_table = sa.table(
        'groups',
        sa.column('id', sa.Integer),
        sa.column('name', sa.String),
        sa.column('owner_id', sa.Integer),
        sa.column('created_at', sa.DateTime),
        sa.column('updated_at', sa.DateTime),
    )
    
    connection.execute(
        groups_table.insert().values([
            {
                'name': 'Семейный бюджет',
                'owner_id': user_ids['ivanov'],
                'created_at': now,
                'updated_at': now,
            },
            {
                'name': 'Рабочая группа',
                'owner_id': user_ids['petrova'],
                'created_at': now,
                'updated_at': now,
            },
        ])
    )
    
    # Получаем ID созданных групп
    result = connection.execute(
        sa.text("SELECT id, name FROM groups ORDER BY name")
    )
    group_ids = {row[1]: row[0] for row in result}
    
    # Создание связей пользователей с группами
    user_groups_table = sa.table(
        'user_groups',
        sa.column('id', sa.Integer),
        sa.column('user_id', sa.Integer),
        sa.column('group_id', sa.Integer),
        sa.column('role', sa.Enum),
        sa.column('joined_at', sa.DateTime),
        sa.column('created_at', sa.DateTime),
        sa.column('updated_at', sa.DateTime),
    )
    
    connection.execute(
        user_groups_table.insert().values([
            # Семейный бюджет: Иван (owner), Мария (member)
            {
                'user_id': user_ids['ivanov'],
                'group_id': group_ids['Семейный бюджет'],
                'role': 'OWNER',
                'joined_at': now,
                'created_at': now,
                'updated_at': now,
            },
            {
                'user_id': user_ids['petrova'],
                'group_id': group_ids['Семейный бюджет'],
                'role': 'MEMBER',
                'joined_at': now,
                'created_at': now,
                'updated_at': now,
            },
            # Рабочая группа: Мария (owner), Алексей и Елена (members)
            {
                'user_id': user_ids['petrova'],
                'group_id': group_ids['Рабочая группа'],
                'role': 'OWNER',
                'joined_at': now,
                'created_at': now,
                'updated_at': now,
            },
            {
                'user_id': user_ids['sidorov'],
                'group_id': group_ids['Рабочая группа'],
                'role': 'MEMBER',
                'joined_at': now,
                'created_at': now,
                'updated_at': now,
            },
            {
                'user_id': user_ids['kozlova'],
                'group_id': group_ids['Рабочая группа'],
                'role': 'MEMBER',
                'joined_at': now,
                'created_at': now,
                'updated_at': now,
            },
        ])
    )
    
    # Создание транзакций
    transactions_table = sa.table(
        'transactions',
        sa.column('id', sa.Integer),
        sa.column('name', sa.String),
        sa.column('type', sa.Enum),
        sa.column('category', sa.String),
        sa.column('amount', sa.Float),
        sa.column('date', sa.Date),
        sa.column('user_id', sa.Integer),
        sa.column('group_id', sa.Integer),
        sa.column('created_at', sa.DateTime),
        sa.column('updated_at', sa.DateTime),
    )
    
    today = date.today()
    
    connection.execute(
        transactions_table.insert().values([
            # Доходы Ивана
            {
                'name': 'Зарплата',
                'type': 'INCOME',
                'category': 'Работа',
                'amount': 100000.0,
                'date': today,
                'user_id': user_ids['ivanov'],
                'group_id': None,
                'created_at': now,
                'updated_at': now,
            },
            {
                'name': 'Премия',
                'type': 'INCOME',
                'category': 'Работа',
                'amount': 20000.0,
                'date': today,
                'user_id': user_ids['ivanov'],
                'group_id': None,
                'created_at': now,
                'updated_at': now,
            },
            # Расходы Ивана
            {
                'name': 'Продукты',
                'type': 'EXPENSE',
                'category': 'Еда',
                'amount': 5000.0,
                'date': today,
                'user_id': user_ids['ivanov'],
                'group_id': group_ids['Семейный бюджет'],
                'created_at': now,
                'updated_at': now,
            },
            {
                'name': 'Транспорт',
                'type': 'EXPENSE',
                'category': 'Транспорт',
                'amount': 2000.0,
                'date': today,
                'user_id': user_ids['ivanov'],
                'group_id': None,
                'created_at': now,
                'updated_at': now,
            },
            # Доходы Марии
            {
                'name': 'Зарплата',
                'type': 'INCOME',
                'category': 'Работа',
                'amount': 80000.0,
                'date': today,
                'user_id': user_ids['petrova'],
                'group_id': None,
                'created_at': now,
                'updated_at': now,
            },
            # Расходы Марии
            {
                'name': 'Одежда',
                'type': 'EXPENSE',
                'category': 'Покупки',
                'amount': 10000.0,
                'date': today,
                'user_id': user_ids['petrova'],
                'group_id': group_ids['Семейный бюджет'],
                'created_at': now,
                'updated_at': now,
            },
            {
                'name': 'Коммунальные услуги',
                'type': 'EXPENSE',
                'category': 'Жилье',
                'amount': 8000.0,
                'date': today,
                'user_id': user_ids['petrova'],
                'group_id': group_ids['Рабочая группа'],
                'created_at': now,
                'updated_at': now,
            },
            # Доходы Алексея
            {
                'name': 'Фриланс',
                'type': 'INCOME',
                'category': 'Работа',
                'amount': 30000.0,
                'date': today,
                'user_id': user_ids['sidorov'],
                'group_id': None,
                'created_at': now,
                'updated_at': now,
            },
            # Расходы Алексея
            {
                'name': 'Развлечения',
                'type': 'EXPENSE',
                'category': 'Досуг',
                'amount': 5000.0,
                'date': today,
                'user_id': user_ids['sidorov'],
                'group_id': group_ids['Рабочая группа'],
                'created_at': now,
                'updated_at': now,
            },
            # Доходы Елены
            {
                'name': 'Зарплата',
                'type': 'INCOME',
                'category': 'Работа',
                'amount': 70000.0,
                'date': today,
                'user_id': user_ids['kozlova'],
                'group_id': None,
                'created_at': now,
                'updated_at': now,
            },
            # Расходы Елены
            {
                'name': 'Образование',
                'type': 'EXPENSE',
                'category': 'Образование',
                'amount': 15000.0,
                'date': today,
                'user_id': user_ids['kozlova'],
                'group_id': group_ids['Рабочая группа'],
                'created_at': now,
                'updated_at': now,
            },
        ])
    )


def downgrade() -> None:
    """Удалить тестовые данные из базы."""
    connection = op.get_bind()
    
    # Удаление транзакций тестовых пользователей
    connection.execute(
        sa.text("DELETE FROM transactions WHERE user_id IN (SELECT id FROM users WHERE login IN ('ivanov', 'petrova', 'sidorov', 'kozlova'))")
    )
    
    # Удаление связей пользователей с группами
    connection.execute(
        sa.text("DELETE FROM user_groups WHERE user_id IN (SELECT id FROM users WHERE login IN ('ivanov', 'petrova', 'sidorov', 'kozlova'))")
    )
    
    # Удаление групп
    connection.execute(
        sa.text("DELETE FROM groups WHERE name IN ('Семейный бюджет', 'Рабочая группа')")
    )
    
    # Удаление тестовых пользователей
    connection.execute(
        sa.text("DELETE FROM users WHERE login IN ('ivanov', 'petrova', 'sidorov', 'kozlova')")
    )

