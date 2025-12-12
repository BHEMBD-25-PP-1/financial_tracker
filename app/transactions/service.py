"""Сервисный слой для Transactions API."""

from datetime import date
from typing import Optional, Tuple

from sqlalchemy.orm import Session

from app.db.models import TransactionType as DBTransactionType
from app.repositories.transaction_repository import TransactionRepository
from app.transactions.models import (
    Transaction,
    TransactionCategory,
    TransactionType,
)


class TransactionService:
    """Сервис для работы с транзакциями."""

    def __init__(self, db: Session):
        """Инициализация сервиса."""
        self.db = db
        self.transaction_repository = TransactionRepository(db)

    def _convert_db_transaction_to_model(self, db_transaction) -> Transaction:
        """Преобразовать транзакцию из БД в модель API."""
        # Преобразуем тип транзакции из enum БД в enum модели
        type_value = None
        
        # Пробуем разные способы получения значения типа транзакции
        try:
            if isinstance(db_transaction.type, str):
                # Это уже строка
                type_value = db_transaction.type
            elif isinstance(db_transaction.type, DBTransactionType):
                # Это enum из БД, берем его значение
                type_value = db_transaction.type.value
            elif hasattr(db_transaction.type, 'value'):
                # Это enum, пробуем получить value
                type_value = db_transaction.type.value
            elif hasattr(db_transaction.type, 'name'):
                # Это enum, пробуем через name и преобразуем в значение
                name = db_transaction.type.name
                if name == "INCOME":
                    type_value = "income"
                elif name == "EXPENSE":
                    type_value = "expense"
                else:
                    type_value = name.lower()
            else:
                # Пытаемся преобразовать в строку
                type_value = str(db_transaction.type)
        except Exception as e:
            # Если ничего не сработало, пробуем получить строковое представление
            type_value = str(db_transaction.type)

        # Нормализуем значение: приводим к lowercase для совместимости
        if isinstance(type_value, str):
            type_value_lower = type_value.lower()
        else:
            type_value_lower = str(type_value).lower()
        
        # Преобразуем в enum модели API (значения там lowercase: "income", "expense")
        if type_value_lower == "income":
            trans_type = TransactionType.INCOME
        elif type_value_lower == "expense":
            trans_type = TransactionType.EXPENSE
        else:
            # Если ничего не подошло, пробуем создать напрямую
            try:
                trans_type = TransactionType(type_value_lower)
            except ValueError:
                raise ValueError(f"Unknown transaction type: {type_value} (normalized: {type_value_lower}). Transaction ID: {db_transaction.id}")
        
        trans_category = TransactionCategory(db_transaction.category)

        return Transaction(
            id=db_transaction.id,
            name=db_transaction.name,
            type=trans_type,
            category=trans_category,
            amount=db_transaction.amount,
            date=db_transaction.date,
            user_id=db_transaction.user_id,
            group_id=db_transaction.group_id,
            created_at=db_transaction.created_at,
            updated_at=db_transaction.updated_at
        )

    def get_transactions(
        self,
        user_id: int,
        page: int = 1,
        size: int = 20,
        category: Optional[TransactionCategory] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        group_id: Optional[int] = None,
        transaction_type: Optional[TransactionType] = None
    ) -> Tuple[list[Transaction], int]:
        """Получить список транзакций с пагинацией и фильтрами.

        Args:
            user_id: ID пользователя
            page: Номер страницы
            size: Размер страницы
            category: Фильтр по категории
            start_date: Дата начала периода
            end_date: Дата окончания периода
            group_id: Фильтр по группе
            transaction_type: Фильтр по типу транзакции

        Returns:
            Tuple: (Список транзакций, общее количество)
        """
        skip = (page - 1) * size

        # Преобразуем enum в значение для репозитория
        category_value = category.value if category else None
        transaction_type_value = None
        if transaction_type:
            # Преобразуем TransactionType в DBTransactionType
            transaction_type_value = DBTransactionType(transaction_type.value)

        transactions, total = self.transaction_repository.get_all(
            user_id=user_id,
            skip=skip,
            limit=size,
            category=category_value,
            start_date=start_date,
            end_date=end_date,
            group_id=group_id,
            transaction_type=transaction_type_value
        )

        transaction_items = [
            self._convert_db_transaction_to_model(t) for t in transactions
        ]

        return transaction_items, total

    def create_transaction(
        self,
        name: str,
        transaction_type: TransactionType,
        category: str,
        amount: float,
        transaction_date: date,
        user_id: int,
        group_id: Optional[int] = None
    ) -> Transaction:
        """Создать новую транзакцию.

        Args:
            name: Название транзакции
            transaction_type: Тип транзакции
            category: Категория транзакции (строка)
            amount: Сумма транзакции
            transaction_date: Дата транзакции
            user_id: ID пользователя
            group_id: ID группы (опционально)

        Returns:
            Transaction: Созданная транзакция

        Raises:
            ValueError: При ошибке валидации
            RuntimeError: При ошибке базы данных
        """
        # Валидируем категорию - преобразуем строку в enum для проверки
        try:
            category_enum = TransactionCategory(category)
        except ValueError:
            valid_categories = [cat.value for cat in TransactionCategory]
            raise ValueError(
                f"Недопустимая категория '{category}'. "
                f"Допустимые значения: {', '.join(valid_categories)}"
            )
        
        # Преобразуем TransactionType в DBTransactionType
        db_transaction_type = DBTransactionType(transaction_type.value)

        transaction = self.transaction_repository.create(
            name=name,
            type=db_transaction_type,
            category=category_enum.value,
            amount=amount,
            transaction_date=transaction_date,
            user_id=user_id,
            group_id=group_id
        )

        return self._convert_db_transaction_to_model(transaction)

    def get_transaction_by_id(self, transaction_id: int, user_id: int) -> Optional[Transaction]:
        """Получить транзакцию по ID.

        Args:
            transaction_id: ID транзакции
            user_id: ID пользователя

        Returns:
            Transaction: Транзакция или None если не найдена
        """
        transaction = self.transaction_repository.get_by_id(transaction_id, user_id=user_id)
        if not transaction:
            return None

        return self._convert_db_transaction_to_model(transaction)

    def update_transaction(
        self,
        transaction_id: int,
        user_id: int,
        name: Optional[str] = None,
        amount: Optional[float] = None,
        category: Optional[TransactionCategory] = None,
        date: Optional[date] = None,
        transaction_type: Optional[TransactionType] = None,
        group_id: Optional[int] = None
    ) -> Optional[Transaction]:
        """Обновить транзакцию.

        Args:
            transaction_id: ID транзакции
            user_id: ID пользователя
            name: Новое название транзакции
            amount: Новая сумма транзакции
            category: Новая категория транзакции
            date: Новая дата транзакции
            transaction_type: Новый тип транзакции
            group_id: Новый ID группы

        Returns:
            Transaction: Обновленная транзакция или None если не найдена

        Raises:
            ValueError: При ошибке валидации
            RuntimeError: При ошибке базы данных
        """
        # Подготавливаем данные для обновления
        update_data = {}

        if name is not None:
            update_data['name'] = name

        if amount is not None:
            update_data['amount'] = amount

        if category is not None:
            # Если category - строка, преобразуем в enum
            if isinstance(category, str):
                try:
                    category_enum = TransactionCategory(category)
                    update_data['category'] = category_enum.value
                except ValueError:
                    valid_categories = [cat.value for cat in TransactionCategory]
                    raise ValueError(
                        f"Недопустимая категория '{category}'. "
                        f"Допустимые значения: {', '.join(valid_categories)}"
                    )
            else:
                update_data['category'] = category.value

        if date is not None:
            update_data['date'] = date

        if transaction_type is not None:
            # Преобразуем TransactionType в DBTransactionType
            update_data['type'] = DBTransactionType(transaction_type.value)

        if group_id is not None:
            update_data['group_id'] = group_id

        transaction = self.transaction_repository.update(
            transaction_id=transaction_id,
            user_id=user_id,
            **update_data
        )

        if not transaction:
            return None

        return self._convert_db_transaction_to_model(transaction)

    def delete_transaction(self, transaction_id: int, user_id: int) -> bool:
        """Удалить транзакцию.

        Args:
            transaction_id: ID транзакции
            user_id: ID пользователя

        Returns:
            bool: True если транзакция удалена

        Raises:
            RuntimeError: При ошибке базы данных
        """
        return self.transaction_repository.delete(transaction_id, user_id)


