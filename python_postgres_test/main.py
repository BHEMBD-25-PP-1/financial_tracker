from user_repository import UserRepository

repo = UserRepository()

# Создание пользователя
new_user = repo.add("Иван", "ivan@example.com")
print("Создан:", new_user)

# Получение по ID
user = repo.get_by_id(new_user.id)
print("Найден по ID:", user)

# Все пользователи
print("Все пользователи:", repo.get_all())

