import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal, Base, engine
from user import User
from user_repository import UserRepository

# Создаем таблицы
Base.metadata.create_all(bind=engine)

# Создаем сессию
db = SessionLocal()

# Создаем репозиторий
user_repo = UserRepository(db)

# Создаем нового пользователя
new_user = User(name="Alice", email="alice@example.com")
created_user = user_repo.create(new_user)
print(f"Created user: {created_user.id}, {created_user.name}, {created_user.email}")

# Получаем пользователя по ID
user = user_repo.get_by_id(created_user.id)
print(f"Fetched user: {user.id}, {user.name}, {user.email}")

