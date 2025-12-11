"""Скрипт для заполнения базы данных тестовыми данными.

Создает 4 пользователя с паролем password123, группы и транзакции.
"""

import sys
from pathlib import Path
from datetime import date, timedelta

# Добавляем корень проекта в путь
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.session import SessionLocal
from app.repositories.user_repository import UserRepository
from app.repositories.group_repository import GroupRepository
from app.repositories.transaction_repository import TransactionRepository
from app.db.models import TransactionType, GroupRole
# Импортируем enum из правильного места для использования в репозитории
from app.repositories.transaction_repository import TransactionRepository

# Тестовые пользователи
USERS = [
    {"first_name": "Иван", "last_name": "Иванов", "login": "ivanov"},
    {"first_name": "Мария", "last_name": "Петрова", "login": "petrova"},
    {"first_name": "Петр", "last_name": "Сидоров", "login": "sidorov"},
    {"first_name": "Анна", "last_name": "Козлова", "login": "kozlova"},
]

PASSWORD = "password123"

# Категории транзакций
CATEGORIES = [
    "Продукты",
    "Одежда и обувь",
    "Дом и ремонт",
    "Путешествия",
    "Переводы",
    "Косметика и бытовая химия",
    "Спорт",
    "Развлечения",
    "Кафе и рестораны",
]


def create_users(db_session):
    """Создать тестовых пользователей."""
    print("Создание пользователей...")
    user_repo = UserRepository(db_session)
    users = []
    
    for user_data in USERS:
        try:
            # Проверяем, существует ли пользователь
            existing_user = user_repo.get_by_login(user_data["login"])
            if existing_user:
                users.append(existing_user)
                print(f"  [SKIP] Пользователь уже существует: {existing_user.login} (ID: {existing_user.id})")
            else:
                user = user_repo.add(
                    first_name=user_data["first_name"],
                    last_name=user_data["last_name"],
                    login=user_data["login"],
                    password=PASSWORD
                )
                users.append(user)
                print(f"  [OK] Создан пользователь: {user.login} (ID: {user.id})")
        except Exception as e:
            print(f"  [ERROR] Ошибка при создании пользователя {user_data['login']}: {e}")
    
    return users


def create_groups(db_session, users):
    """Создать тестовые группы."""
    print("\nСоздание групп...")
    group_repo = GroupRepository(db_session)
    groups = []
    
    # Семейная группа (Ивановы)
    if len(users) >= 2:
        try:
            family_group = group_repo.create(
                name="Семья Ивановых",
                owner_id=users[0].id
            )
            groups.append(family_group)
            print(f"  [OK] Создана группа: {family_group.name} (ID: {family_group.id})")
            
            # Добавляем второго пользователя в группу
            group_repo.add_member(
                group_id=family_group.id,
                user_id=users[1].id,
                owner_id=users[0].id,
                role=GroupRole.MEMBER
            )
            print(f"  [OK] Добавлен участник {users[1].login} в группу {family_group.name}")
        except Exception as e:
            print(f"  [ERROR] Ошибка при создании группы: {e}")
    
    # Группа друзей
    if len(users) >= 3:
        try:
            friends_group = group_repo.create(
                name="Друзья",
                owner_id=users[2].id
            )
            groups.append(friends_group)
            print(f"  [OK] Создана группа: {friends_group.name} (ID: {friends_group.id})")
            
            # Добавляем других пользователей в группу
            for user in users[:3]:
                if user.id != users[2].id:
                    try:
                        group_repo.add_member(
                            group_id=friends_group.id,
                            user_id=user.id,
                            owner_id=users[2].id,
                            role=GroupRole.MEMBER
                        )
                        print(f"  [OK] Добавлен участник {user.login} в группу {friends_group.name}")
                    except Exception as e:
                        print(f"  [ERROR] Ошибка при добавлении участника: {e}")
        except Exception as e:
            print(f"  [ERROR] Ошибка при создании группы: {e}")
    
    return groups


def create_transactions(db_session, users, groups):
    """Создать тестовые транзакции."""
    print("\nСоздание транзакций...")
    transaction_repo = TransactionRepository(db_session)
    
    # Даты для транзакций (последние 30 дней)
    today = date.today()
    dates = [today - timedelta(days=i) for i in range(30)]
    
    transaction_count = 0
    
    # Создаем транзакции для каждого пользователя
    for user in users:
        # Личные транзакции (без группы)
        for i in range(5):
            try:
                # Используем правильные значения enum (lowercase)
                trans_type = TransactionType.EXPENSE if i % 2 == 0 else TransactionType.INCOME
                transaction_repo.create(
                    name=f"Покупка {CATEGORIES[i % len(CATEGORIES)]}",
                    type=trans_type,
                    category=CATEGORIES[i % len(CATEGORIES)],
                    amount=round(100.0 + (i * 50.5), 2),
                    transaction_date=dates[i * 2],
                    user_id=user.id,
                    group_id=None
                )
                transaction_count += 1
            except Exception as e:
                print(f"  [ERROR] Ошибка при создании транзакции: {e}")
        
        # Групповые транзакции (если есть группы)
        if groups:
            for group in groups:
                # Проверяем, является ли пользователь участником группы
                from app.db.models import UserGroup
                user_group = db_session.query(UserGroup).filter(
                    UserGroup.user_id == user.id,
                    UserGroup.group_id == group.id
                ).first()
                
                if user_group:
                    try:
                        transaction_repo.create(
                            name=f"Совместная покупка для {group.name}",
                            type=TransactionType.EXPENSE,  # Используем enum напрямую
                            category=CATEGORIES[0],  # Продукты
                            amount=round(500.0 + (transaction_count * 10), 2),
                            transaction_date=dates[transaction_count % len(dates)],
                            user_id=user.id,
                            group_id=group.id
                        )
                        transaction_count += 1
                    except Exception as e:
                        print(f"  [ERROR] Ошибка при создании групповой транзакции: {e}")
    
    print(f"  [OK] Создано транзакций: {transaction_count}")


def main():
    """Основная функция для заполнения БД."""
    print("=" * 60)
    print("Заполнение базы данных тестовыми данными")
    print("=" * 60)
    
    db_session = SessionLocal()
    
    try:
        # Создаем пользователей
        users = create_users(db_session)
        
        if not users:
            print("\nОшибка: не удалось создать пользователей")
            return
        
        # Создаем группы
        groups = create_groups(db_session, users)
        
        # Создаем транзакции
        create_transactions(db_session, users, groups)
        
        print("\n" + "=" * 60)
        print("Заполнение базы данных завершено успешно!")
        print("=" * 60)
        print(f"\nСоздано:")
        print(f"  - Пользователей: {len(users)}")
        print(f"  - Групп: {len(groups)}")
        print(f"\nВсе пользователи имеют пароль: {PASSWORD}")
        
    except Exception as e:
        print(f"\nОшибка при заполнении БД: {e}")
        db_session.rollback()
        raise
    finally:
        db_session.close()


if __name__ == "__main__":
    main()

