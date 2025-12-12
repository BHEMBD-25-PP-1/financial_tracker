"""Репозиторий для работы с транзакциями в базе данных."""

from contextlib import contextmanager
from datetime import date
from typing import List, Optional

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.models import Transaction, User, Group, TransactionType
from app.db.session import SessionLocal
from app.repositories.base_repository import BaseRepository


class TransactionRepository(BaseRepository[Transaction]):
    """Репозиторий для работы с транзакциями."""

    def __init__(self, db_session: Optional[Session] = None):
        """Инициализация репозитория."""
        self.db = db_session or SessionLocal()
        self._owns_session = db_session is None
        self._logger = None
        super().__init__(Transaction, self.db)

    def __enter__(self):
        """Вход в context manager."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Выход из context manager."""
        if self._owns_session:
            self.db.close()

    @property
    def logger(self):
        """Логгер для репозитория."""
        if self._logger is None:
            import logging
            self._logger = logging.getLogger(__name__)
        return self._logger

    @contextmanager
    def _transaction(self):
        """Context manager для управления транзакциями."""
        try:
            yield self.db
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"Transaction failed: {e}")
            raise

    @staticmethod
    def _validate_transaction_data(
        name: str,
        amount: float,
        category: str,
        transaction_date: date
    ) -> None:
        """Валидация данных транзакции."""
        if not name or not name.strip():
            raise ValueError("Transaction name cannot be empty")
        if len(name.strip()) > 255:
            raise ValueError("Transaction name too long (max 255 characters)")
        
        if amount <= 0:
            raise ValueError("Transaction amount must be positive")
        
        if not category or not category.strip():
            raise ValueError("Transaction category cannot be empty")
        if len(category.strip()) > 100:
            raise ValueError("Category too long (max 100 characters)")
        
        if transaction_date > date.today():
            raise ValueError("Transaction date cannot be in the future")

    def create(
        self,
        name: str,
        type: TransactionType,
        category: str,
        amount: float,
        transaction_date: date,
        user_id: int,
        group_id: Optional[int] = None
    ) -> Transaction:
        """Создать новую транзакцию."""
        self.logger.info(
            f"Creating transaction: user_id={user_id}, "
            f"type={type}, amount={amount}, category={category}"
        )
        
        self._validate_transaction_data(
            name=name,
            amount=amount,
            category=category,
            transaction_date=transaction_date
        )

        try:
            with self._transaction():
                # Проверяем существование пользователя
                user = self.db.query(User).filter(User.id == user_id).first()
                if not user:
                    raise ValueError(f"User with ID {user_id} not found")
                
                # Проверяем существование группы, если указана
                if group_id:
                    group = self.db.query(Group).filter(Group.id == group_id).first()
                    if not group:
                        raise ValueError(f"Group with ID {group_id} not found")
                
                transaction = Transaction(
                    name=name.strip(),
                    type=type,
                    category=category.strip(),
                    amount=float(amount),
                    date=transaction_date,
                    user_id=user_id,
                    group_id=group_id
                )
                
                self.db.add(transaction)
                self.db.flush()
                self.logger.info(f"Transaction created successfully with id: {transaction.id}")
                return transaction
                
        except IntegrityError as e:
            self.logger.error(f"Failed to create transaction: {e}")
            raise ValueError(f"Database integrity error: {e}") from e
        except SQLAlchemyError as e:
            self.logger.error(f"Database error while creating transaction: {e}")
            raise RuntimeError(f"Database error: {e}") from e
        except ValueError as e:
            self.logger.error(f"Validation error while creating transaction: {e}")
            raise

    def get_by_id(self, transaction_id: int, user_id: Optional[int] = None) -> Optional[Transaction]:
        """Получить транзакцию по ID."""
        self.logger.debug(f"Fetching transaction by id: {transaction_id}")
        
        try:
            query = self.db.query(Transaction).filter(Transaction.id == transaction_id)
            if user_id:
                query = query.filter(Transaction.user_id == user_id)
            
            transaction = query.first()
            if transaction:
                self.logger.debug(f"Transaction found: id={transaction.id}")
            else:
                self.logger.debug(f"Transaction not found: id={transaction_id}")
            return transaction
        except SQLAlchemyError as e:
            self.logger.error(f"Database error while fetching transaction by id {transaction_id}: {e}")
            raise RuntimeError(f"Database error: {e}") from e

    def get_all(
        self,
        user_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100,
        category: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        group_id: Optional[int] = None,
        transaction_type: Optional[TransactionType] = None
    ) -> tuple[List[Transaction], int]:
        """Получить транзакции с фильтрацией и пагинацией.
        
        Args:
            user_id: ID пользователя
            skip: Количество пропущенных записей
            limit: Максимальное количество записей
            category: Фильтр по категории
            start_date: Дата начала периода
            end_date: Дата окончания периода
            group_id: Фильтр по группе
            transaction_type: Фильтр по типу транзакции
            
        Returns:
            tuple: (Список транзакций, общее количество)
        """
        self.logger.debug(f"Fetching transactions: user_id={user_id}, skip={skip}, limit={limit}")
        
        try:
            query = self.db.query(Transaction)
            
            if user_id:
                query = query.filter(Transaction.user_id == user_id)
            
            if category:
                query = query.filter(Transaction.category == category)
            
            if start_date:
                query = query.filter(Transaction.date >= start_date)
            
            if end_date:
                query = query.filter(Transaction.date <= end_date)
            
            if group_id is not None:
                query = query.filter(Transaction.group_id == group_id)
            
            if transaction_type:
                query = query.filter(Transaction.type == transaction_type)
            
            # Получаем общее количество
            total = query.count()
            
            # Применяем пагинацию и сортировку
            transactions = query.order_by(Transaction.date.desc(), Transaction.id.desc()).offset(skip).limit(limit).all()
            
            self.logger.debug(f"Found {len(transactions)} transactions (total: {total})")
            return transactions, total
        except SQLAlchemyError as e:
            self.logger.error(f"Database error while fetching transactions: {e}")
            raise RuntimeError(f"Database error: {e}") from e

    def update(
        self,
        transaction_id: int,
        user_id: int,
        **kwargs
    ) -> Optional[Transaction]:
        """Обновить транзакцию."""
        self.logger.info(f"Updating transaction: id={transaction_id}, user_id={user_id}")
        
        try:
            with self._transaction():
                query = self.db.query(Transaction).filter(Transaction.id == transaction_id)
                if user_id:
                    query = query.filter(Transaction.user_id == user_id)
                
                transaction = query.first()
                if not transaction:
                    self.logger.warning(f"Transaction not found or access denied: id={transaction_id}, user_id={user_id}")
                    return None
                
                # Валидируем и обновляем поля
                update_data = {}
                
                if 'name' in kwargs:
                    if not kwargs['name'] or not kwargs['name'].strip():
                        raise ValueError("Transaction name cannot be empty")
                    update_data['name'] = kwargs['name'].strip()
                
                if 'amount' in kwargs and kwargs['amount'] is not None:
                    if kwargs['amount'] <= 0:
                        raise ValueError("Transaction amount must be positive")
                    update_data['amount'] = float(kwargs['amount'])
                
                if 'category' in kwargs:
                    if not kwargs['category'] or not kwargs['category'].strip():
                        raise ValueError("Transaction category cannot be empty")
                    update_data['category'] = kwargs['category'].strip()
                
                if 'date' in kwargs and kwargs['date']:
                    if kwargs['date'] > date.today():
                        raise ValueError("Transaction date cannot be in the future")
                    update_data['date'] = kwargs['date']
                
                if 'type' in kwargs and kwargs['type']:
                    update_data['type'] = kwargs['type']
                
                if 'group_id' in kwargs:
                    group_id = kwargs['group_id']
                    if group_id is not None:
                        # Проверяем существование группы
                        group = self.db.query(Group).filter(Group.id == group_id).first()
                        if not group:
                            raise ValueError(f"Group with ID {group_id} not found")
                    update_data['group_id'] = group_id
                
                # Применяем обновления
                for field, value in update_data.items():
                    setattr(transaction, field, value)
                
                self.db.flush()
                self.logger.info(f"Transaction updated successfully: id={transaction.id}")
                
                return transaction
                
        except ValueError as e:
            self.logger.error(f"Validation error while updating transaction {transaction_id}: {e}")
            raise
        except SQLAlchemyError as e:
            self.logger.error(f"Database error while updating transaction {transaction_id}: {e}")
            raise RuntimeError(f"Database error: {e}") from e

    def delete(self, transaction_id: int, user_id: int) -> bool:
        """Удалить транзакцию."""
        self.logger.info(f"Deleting transaction: id={transaction_id}, user_id={user_id}")
        
        try:
            with self._transaction():
                query = self.db.query(Transaction).filter(Transaction.id == transaction_id)
                if user_id:
                    query = query.filter(Transaction.user_id == user_id)
                
                transaction = query.first()
                if not transaction:
                    self.logger.warning(f"Transaction not found or access denied: id={transaction_id}, user_id={user_id}")
                    return False
                
                self.db.delete(transaction)
                self.db.flush()
                self.logger.info(f"Transaction deleted successfully: id={transaction_id}")
                return True
        except SQLAlchemyError as e:
            self.logger.error(f"Database error while deleting transaction {transaction_id}: {e}")
            raise RuntimeError(f"Database error: {e}") from e

    def close(self):
        """Закрыть сессию базы данных."""
        if self._owns_session:
            self.db.close()
            self.logger.debug("Database session closed")
